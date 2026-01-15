import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from config import get_async_session, settings
from config.database import Base
from models import EmailVerificationCode, User
from routers import auth as auth_router


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
    app.include_router(auth_router.router, prefix="/api/auth")

    async def override_get_async_session():
        async with db_sessionmaker() as session:
            yield session

    app.dependency_overrides[get_async_session] = override_get_async_session
    return app


@pytest_asyncio.fixture
async def client(test_app, monkeypatch):
    monkeypatch.setattr(settings, "smtp_host", "smtp.example.com")
    monkeypatch.setattr(settings, "smtp_user", "noreply@example.com")
    monkeypatch.setattr(settings, "smtp_password", "dummy-password")
    monkeypatch.setattr(
        auth_router, "send_email_code_smtp", lambda *args, **kwargs: None
    )

    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_send_email_code_register_success_persists_row(
    client, db_sessionmaker, monkeypatch
):
    monkeypatch.setattr(settings, "email_code_resend_interval_seconds", 0)

    resp = await client.post(
        "/api/auth/send-email-code",
        json={"email": "TeSt@Example.Com", "purpose": "register"},
        headers={"x-forwarded-for": "203.0.113.9"},
    )
    body = resp.json()
    assert body["code"] == 200

    async with db_sessionmaker() as session:
        rows = (
            (
                await session.execute(
                    select(EmailVerificationCode).where(
                        EmailVerificationCode.email == "test@example.com",
                        EmailVerificationCode.purpose == "register",
                    )
                )
            )
            .scalars()
            .all()
        )
        assert len(rows) == 1
        assert rows[0].used_at is None
        assert rows[0].code_hash
        assert rows[0].ip == "203.0.113.9"


@pytest.mark.asyncio
async def test_send_email_code_resend_interval_blocks_second_request(
    client, monkeypatch
):
    monkeypatch.setattr(settings, "email_code_resend_interval_seconds", 60)

    first = await client.post(
        "/api/auth/send-email-code",
        json={"email": "user@example.com", "purpose": "register"},
    )
    assert first.json()["code"] == 200

    second = await client.post(
        "/api/auth/send-email-code",
        json={"email": "user@example.com", "purpose": "register"},
    )
    body = second.json()
    assert body["code"] == 400
    assert "频繁" in body["message"]


@pytest.mark.asyncio
async def test_send_email_code_rejects_unknown_purpose(client):
    resp = await client.post(
        "/api/auth/send-email-code",
        json={"email": "user2@example.com", "purpose": "unknown"},
    )
    body = resp.json()
    assert body["code"] == 400
    assert body["message"] == "不支持的验证码用途"


@pytest.mark.asyncio
async def test_send_email_code_reset_password_requires_existing_email(
    client, db_sessionmaker, monkeypatch
):
    monkeypatch.setattr(settings, "email_code_resend_interval_seconds", 0)

    async with db_sessionmaker() as session:
        session.add(
            User(
                username="existing_user",
                email="exists@example.com",
                status=1,
                user_type=1,
            )
        )
        await session.commit()

    ok = await client.post(
        "/api/auth/send-email-code",
        json={"email": "exists@example.com", "purpose": "reset_password"},
    )
    assert ok.json()["code"] == 200

    bad = await client.post(
        "/api/auth/send-email-code",
        json={"email": "missing@example.com", "purpose": "reset_password"},
    )
    body = bad.json()
    assert body["code"] == 400
    assert body["message"] == "邮箱不存在"
