from typing import Optional

from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, PlainTextResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from config import get_async_session, settings
from models import Order, User, Member, PointTransaction
from routers.auth import get_current_user
from routers.orders import PRODUCTS
from utils.alipay_client import build_pay_url
from utils.alipay_sign import verify_alipay_sign
from utils.logger import get_logger
from utils.response import success, error, not_found
from utils.security import generate_order_no


logger = get_logger(__name__)
router = APIRouter()


class AlipayCreateRequest(BaseModel):
    product_id: int = Field(...)
    amount: Optional[float] = Field(default=None)
    client_type: Optional[str] = Field(default="h5")


@router.post("/alipay/create", summary="创建支付宝充值订单")
async def create_alipay_recharge(
    payload: AlipayCreateRequest,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    if (
        not settings.alipay_app_id
        or not settings.alipay_private_key_path
        or not settings.alipay_alipay_public_key_path
        or not settings.alipay_notify_url
        or not settings.alipay_return_url
    ):
        return error("支付宝支付未配置，请联系管理员")

    product = next((p for p in PRODUCTS if p["id"] == payload.product_id), None)
    if not product:
        return not_found("产品不存在")

    if product.get("type") != "points":
        return error("暂不支持该产品类型通过支付宝充值")

    price = float(product["price"])
    if payload.amount is not None and float(payload.amount) != price:
        return error("金额与产品配置不一致")

    order_no = generate_order_no()

    order = Order(
        order_no=order_no,
        user_id=current_user.id,
        product_id=product["id"],
        product_type=product["type"],
        amount=Decimal(str(price)),
        quantity=1,
        status=1,
        description=f"支付宝充值：{product['name']}",
    )
    db.add(order)
    await db.commit()
    await db.refresh(order)

    try:
        pay_url, alipay_scheme = build_pay_url(
            out_trade_no=order.order_no,
            total_amount=f"{price:.2f}",
            subject=product["name"],
            notify_url=settings.alipay_notify_url,
            return_url=settings.alipay_return_url,
            client_type=(payload.client_type or "h5"),
        )
    except Exception as exc:
        logger.error(f"创建支付宝支付链接失败: {exc}")
        return error("创建支付宝支付链接失败")

    return success(
        {
            "order_id": order.id,
            "order_no": order.order_no,
            "pay_url": pay_url,
            "alipay_scheme": alipay_scheme,
        },
        "创建支付宝充值订单成功",
    )


@router.get("/alipay/return", summary="支付宝同步回调")
async def alipay_return(request: Request):
    params = dict(request.query_params)
    logger.info(f"支付宝同步回调参数: {params}")

    if not verify_alipay_sign(params):
        return HTMLResponse("<h1>验签失败</h1>", status_code=400)

    app_id = params.get("app_id")
    if app_id and settings.alipay_app_id and app_id != settings.alipay_app_id:
        logger.warning(f"同步回调 app_id 不匹配: {app_id}")
        return HTMLResponse("<h1>app_id 不匹配</h1>", status_code=400)

    out_trade_no = params.get("out_trade_no")
    trade_status = params.get("trade_status")

    if trade_status in ("TRADE_SUCCESS", "TRADE_FINISHED"):
        body = f"<h1>支付成功</h1><p>订单号: {out_trade_no}</p>"
    else:
        body = f"<h1>支付未完成</h1><p>订单号: {out_trade_no}</p><p>状态: {trade_status}</p>"

    return HTMLResponse(body)


@router.post("/alipay/notify", summary="支付宝异步通知")
async def alipay_notify(
    request: Request, db: AsyncSession = Depends(get_async_session)
):
    form = await request.form()
    data = dict(form)
    logger.info(f"支付宝异步通知参数: {data}")

    if not verify_alipay_sign(data):
        logger.warning("异步通知验签失败")
        return PlainTextResponse("failure")

    app_id = data.get("app_id")
    if app_id and settings.alipay_app_id and app_id != settings.alipay_app_id:
        logger.warning(f"异步通知 app_id 不匹配: {app_id}")
        return PlainTextResponse("failure")

    out_trade_no = data.get("out_trade_no")
    trade_status = data.get("trade_status")
    total_amount = data.get("total_amount")

    if not out_trade_no or not total_amount:
        logger.warning("异步通知缺少必要字段")
        return PlainTextResponse("failure")

    result = await db.execute(
        select(Order)
        .where(Order.order_no == out_trade_no)
        .options(selectinload(Order.user).selectinload(User.member))
    )
    order = result.scalar_one_or_none()

    if not order:
        logger.warning(f"未找到对应订单: {out_trade_no}")
        return PlainTextResponse("failure")

    try:
        notified_amount = Decimal(str(total_amount))
    except Exception:
        logger.warning(f"通知金额格式错误: {total_amount}")
        return PlainTextResponse("failure")

    if notified_amount != order.amount:
        logger.warning(
            f"通知金额与订单金额不一致: {notified_amount} != {order.amount} (order_no={order.order_no})"
        )
        return PlainTextResponse("failure")

    if order.status == 2:
        logger.info(f"订单已支付，幂等返回 success: {order.order_no}")
        return PlainTextResponse("success")

    if trade_status not in ("TRADE_SUCCESS", "TRADE_FINISHED"):
        logger.warning(
            f"支付未成功，忽略通知: order_no={order.order_no}, status={trade_status}"
        )
        return PlainTextResponse("failure")

    user = order.user
    member: Optional[Member] = user.member if user else None
    if not member:
        logger.error(f"订单用户没有会员信息，无法发放积分: order_no={order.order_no}")
        return PlainTextResponse("failure")

    product = next(
        (p for p in PRODUCTS if p["id"] == order.product_id and p["type"] == "points"),
        None,
    )
    if not product:
        logger.error(f"无法找到订单对应的点数产品: order_id={order.id}")
        return PlainTextResponse("failure")

    points = int(product.get("points", 0))
    if points <= 0:
        logger.error(f"点数产品配置不正确: product_id={product['id']}")
        return PlainTextResponse("failure")

    member.add_points(points)

    transaction = PointTransaction(
        user_id=user.id,
        type=1,
        points=points,
        balance_after=member.points,
        amount=order.amount,
        description=f"支付宝充值：{order.order_no}",
        related_id=order.id,
        related_type="alipay",
    )
    db.add(transaction)

    order.status = 2
    order.payment_method = "alipay"
    order.payment_time = datetime.utcnow()

    try:
        await db.commit()
    except Exception as exc:
        await db.rollback()
        logger.error(f"支付宝异步通知处理失败: {exc}")
        return PlainTextResponse("failure")

    logger.info(
        f"支付宝异步通知处理成功: order_no={order.order_no}, points={points}, user_id={user.id}"
    )
    return PlainTextResponse("success")

