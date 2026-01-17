from datetime import datetime, timezone

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from config import get_async_session, settings
from config.database import Base
from models import Member, Order, PointTransaction, User
from routers import recharge as recharge_router


@pytest_asyncio.fixture
async def db_sessionmaker():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    sessionmaker = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    try:
        yield sessionmaker
    finally:
        await engine.dispose()


@pytest_asyncio.fixture
async def test_app(db_sessionmaker):
    app = FastAPI()
    app.include_router(recharge_router.router, prefix="/api/recharge")

    async def override_get_async_session():
        async with db_sessionmaker() as session:
            yield session

    app.dependency_overrides[get_async_session] = override_get_async_session
    return app


@pytest_asyncio.fixture
async def client(test_app):
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_create_alipay_recharge_returns_pay_url(
    client, test_app, db_sessionmaker, monkeypatch
):
    monkeypatch.setattr(settings, "alipay_app_id", "test-app-id")
    monkeypatch.setattr(settings, "alipay_private_key_path", "/tmp/merchant.pem")
    monkeypatch.setattr(settings, "alipay_alipay_public_key_path", "/tmp/alipay.pem")
    monkeypatch.setattr(
        settings, "alipay_notify_url", "https://example.com/api/recharge/alipay/notify"
    )
    monkeypatch.setattr(
        settings, "alipay_return_url", "https://example.com/api/recharge/alipay/return"
    )

    monkeypatch.setattr(
        recharge_router,
        "build_pay_url",
        lambda **kwargs: (
            "https://open.alipay.test/pay",
            "alipays://platformapi/startapp?appId=20000067&url=encoded",
        ),
    )

    async with db_sessionmaker() as session:
        user = User(username="member1", email="m1@example.com", status=1, user_type=2)
        session.add(user)
        await session.commit()
        await session.refresh(user)
        user_id = user.id

    async def override_get_current_user():
        return User(
            id=user_id,
            username="member1",
            email="m1@example.com",
            status=1,
            user_type=2,
        )

    test_app.dependency_overrides[
        recharge_router.get_current_user
    ] = override_get_current_user

    resp = await client.post(
        "/api/recharge/alipay/create",
        json={"product_id": 5, "amount": 0.01, "client_type": "h5"},
    )
    body = resp.json()
    assert body["code"] == 200
    assert body["data"]["pay_url"].startswith("https://")
    assert body["data"]["order_id"]
    assert body["data"]["order_no"]

    async with db_sessionmaker() as session:
        row = (
            (
                await session.execute(
                    select(Order).where(Order.order_no == body["data"]["order_no"])
                )
            )
            .scalars()
            .one()
        )
        assert row.user_id == user_id
        assert row.product_id == 5
        assert row.status == 1


@pytest.mark.asyncio
async def test_alipay_notify_is_idempotent_and_adds_points(
    client, db_sessionmaker, monkeypatch
):
    monkeypatch.setattr(settings, "alipay_app_id", "test-app-id")
    monkeypatch.setattr(
        recharge_router, "verify_alipay_sign", lambda *_args, **_kwargs: True
    )

    async with db_sessionmaker() as session:
        user = User(username="member2", email="m2@example.com", status=1, user_type=2)
        session.add(user)
        await session.flush()

        member = Member(user_id=user.id, points=0, balance=0.00)
        session.add(member)
        await session.flush()

        order = Order(
            order_no="ORDER_NO_IDEMPOTENT",
            user_id=user.id,
            product_id=5,
            product_type="points",
            amount=0.01,
            quantity=1,
            status=1,
            description="支付宝充值：小额体验包",
        )
        session.add(order)
        await session.commit()

    data = {
        "app_id": "test-app-id",
        "out_trade_no": "ORDER_NO_IDEMPOTENT",
        "trade_status": "TRADE_SUCCESS",
        "total_amount": "0.01",
        "sign": "dummy",
        "sign_type": "RSA2",
    }

    first = await client.post("/api/recharge/alipay/notify", data=data)
    assert first.text == "success"

    second = await client.post("/api/recharge/alipay/notify", data=data)
    assert second.text == "success"

    async with db_sessionmaker() as session:
        member_points = (
            await session.execute(
                select(Member.points).join(User).where(User.username == "member2")
            )
        ).scalar_one()
        assert member_points == 10

        order_status = (
            await session.execute(
                select(Order.status).where(Order.order_no == "ORDER_NO_IDEMPOTENT")
            )
        ).scalar_one()
        assert order_status == 2

        tx_count = (
            await session.execute(
                select(func.count())
                .select_from(PointTransaction)
                .where(
                    PointTransaction.related_type == "alipay",
                    PointTransaction.description == "支付宝充值：ORDER_NO_IDEMPOTENT",
                )
            )
        ).scalar_one()
        assert tx_count == 1


@pytest.mark.asyncio
async def test_alipay_notify_subscription_sets_expired_at(
    client, db_sessionmaker, monkeypatch
):
    monkeypatch.setattr(settings, "alipay_app_id", "test-app-id")
    monkeypatch.setattr(
        recharge_router, "verify_alipay_sign", lambda *_args, **_kwargs: True
    )

    async with db_sessionmaker() as session:
        user = User(username="member3", email="m3@example.com", status=1, user_type=2)
        session.add(user)
        await session.flush()

        member = Member(user_id=user.id, points=0, balance=0.00, member_level=1)
        session.add(member)
        await session.flush()

        order = Order(
            order_no="ORDER_NO_SUBSCRIPTION",
            user_id=user.id,
            product_id=6,
            product_type="subscription",
            amount=0.01,
            quantity=1,
            status=1,
            description="支付宝购买：15日套餐",
        )
        session.add(order)
        await session.commit()

    data = {
        "app_id": "test-app-id",
        "out_trade_no": "ORDER_NO_SUBSCRIPTION",
        "trade_status": "TRADE_SUCCESS",
        "total_amount": "0.01",
        "sign": "dummy",
        "sign_type": "RSA2",
    }

    resp = await client.post("/api/recharge/alipay/notify", data=data)
    assert resp.text == "success"

    async with db_sessionmaker() as session:
        member_row = (
            (
                await session.execute(
                    select(Member).join(User).where(User.username == "member3")
                )
            )
            .scalars()
            .one()
        )
        assert member_row.member_level >= 2
        assert member_row.expired_at is not None

        expired_at = member_row.expired_at
        if expired_at.tzinfo is None:
            expired_at = expired_at.replace(tzinfo=timezone.utc)

        delta_days = (expired_at - datetime.now(timezone.utc)).days
        assert 13 <= delta_days <= 15
