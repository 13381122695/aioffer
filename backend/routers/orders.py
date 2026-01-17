"""
订单管理路由
创建日期: 2025-01-08
用途: 订单和支付管理功能
"""

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import selectinload

from config import get_async_session
from models import User, Order, PointTransaction
from utils.security import generate_order_no
from utils.response import success, error, not_found, paginated
from utils.logger import get_logger
from routers.auth import get_current_user

logger = get_logger(__name__)
router = APIRouter()


@router.get("/", summary="获取订单列表")
async def get_orders(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=1, le=100, description="每页数量"),
    status: Optional[int] = Query(None, ge=1, le=4, description="订单状态"),
    user_id: Optional[int] = Query(None, description="用户ID"),
    order_no: Optional[str] = Query(None, description="订单号"),
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """获取订单列表"""
    try:
        # 检查权限（管理员可以查看所有订单，普通用户只能查看自己的订单）
        if not current_user.is_admin and user_id and user_id != current_user.id:
            return error("权限不足")

        # 构建查询
        query = select(Order)

        # 应用筛选条件
        if not current_user.is_admin:
            query = query.where(Order.user_id == current_user.id)
        elif user_id:
            query = query.where(Order.user_id == user_id)

        if status is not None:
            query = query.where(Order.status == status)

        if order_no:
            query = query.where(Order.order_no.contains(order_no))

        # 按创建时间降序排列
        query = query.order_by(Order.created_at.desc())

        # 计算总数
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # 分页查询
        offset = (page - 1) * size
        query = query.offset(offset).limit(size)

        result = await db.execute(query.options(selectinload(Order.user)))
        orders = result.scalars().all()

        # 转换为订单响应格式
        order_data = []
        for order in orders:
            order_info = {
                "id": order.id,
                "order_no": order.order_no,
                "user_id": order.user_id,
                "username": order.user.username if order.user else None,
                "product_id": order.product_id,
                "product_type": order.product_type,
                "amount": float(order.amount),
                "quantity": order.quantity,
                "status": order.status,
                "status_text": order.status_text,
                "payment_method": order.payment_method,
                "payment_time": order.payment_time,
                "description": order.description,
                "created_at": order.created_at,
                "updated_at": order.updated_at,
            }
            order_data.append(order_info)

        return paginated(order_data, total, page, size, "获取订单列表成功")

    except Exception as e:
        logger.error(f"获取订单列表失败: {str(e)}")
        return error("获取订单列表失败")


@router.get("/stats", summary="获取订单统计")
async def get_order_stats(
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """获取订单统计"""
    try:
        # 构建基础查询
        query = select(Order)
        if not current_user.is_admin:
            query = query.where(Order.user_id == current_user.id)

        # 总订单数
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total_orders = total_result.scalar() or 0

        # 总金额
        amount_query = select(func.sum(Order.amount)).select_from(query.subquery())
        amount_result = await db.execute(amount_query)
        total_amount = amount_result.scalar() or 0.0

        # 待支付订单
        pending_query = select(func.count()).select_from(
            query.where(Order.status == 1).subquery()
        )
        pending_result = await db.execute(pending_query)
        pending_orders = pending_result.scalar() or 0

        # 已完成订单
        completed_query = select(func.count()).select_from(
            query.where(Order.status == 2).subquery()
        )
        completed_result = await db.execute(completed_query)
        completed_orders = completed_result.scalar() or 0

        return success(
            {
                "total_orders": total_orders,
                "total_amount": float(total_amount),
                "pending_orders": pending_orders,
                "completed_orders": completed_orders,
            },
            "获取订单统计成功",
        )

    except Exception as e:
        logger.error(f"获取订单统计失败: {str(e)}")
        return error("获取订单统计失败")


@router.get("/{order_id}", summary="获取订单详情")
async def get_order_stats(
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """获取订单统计"""
    try:
        # 构建基础查询
        query = select(Order)
        if not current_user.is_admin:
            query = query.where(Order.user_id == current_user.id)

        # 总订单数
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total_orders = total_result.scalar() or 0

        # 总金额
        amount_query = select(func.sum(Order.amount)).select_from(query.subquery())
        amount_result = await db.execute(amount_query)
        total_amount = amount_result.scalar() or 0.0

        # 待支付订单
        pending_query = select(func.count()).select_from(
            query.where(Order.status == 1).subquery()
        )
        pending_result = await db.execute(pending_query)
        pending_orders = pending_result.scalar() or 0

        # 已完成订单
        completed_query = select(func.count()).select_from(
            query.where(Order.status == 2).subquery()
        )
        completed_result = await db.execute(completed_query)
        completed_orders = completed_result.scalar() or 0

        return success(
            {
                "total_orders": total_orders,
                "total_amount": float(total_amount),
                "pending_orders": pending_orders,
                "completed_orders": completed_orders,
            },
            "获取订单统计成功",
        )

    except Exception as e:
        logger.error(f"获取订单统计失败: {str(e)}")
        return error("获取订单统计失败")


@router.get("/{order_id}", summary="获取订单详情")
async def get_order(
    order_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """获取订单详情"""
    try:
        result = await db.execute(
            select(Order).where(Order.id == order_id).options(selectinload(Order.user))
        )
        order = result.scalar_one_or_none()

        if not order:
            return not_found("订单不存在")

        # 检查权限（只能查看自己的订单，除非是管理员）
        if not current_user.is_admin and order.user_id != current_user.id:
            return error("权限不足")

        order_data = {
            "id": order.id,
            "order_no": order.order_no,
            "user_id": order.user_id,
            "username": order.user.username if order.user else None,
            "product_id": order.product_id,
            "product_type": order.product_type,
            "amount": float(order.amount),
            "quantity": order.quantity,
            "status": order.status,
            "status_text": order.status_text,
            "payment_method": order.payment_method,
            "payment_time": order.payment_time,
            "description": order.description,
            "created_at": order.created_at,
            "updated_at": order.updated_at,
            "can_pay": order.can_pay(),
            "can_cancel": order.can_cancel(),
            "can_refund": order.can_refund(),
        }

        return success(order_data, "获取订单详情成功")

    except Exception as e:
        logger.error(f"获取订单详情失败: {str(e)}")
        return error("获取订单详情失败")


@router.post("/", summary="创建订单")
async def create_order(
    request: dict,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """创建订单"""
    try:
        product_type = request.get("product_type")
        product_id = request.get("product_id")
        amount = request.get("amount")
        quantity = request.get("quantity", 1)
        description = request.get("description")

        if not product_type or not amount or amount <= 0:
            return error("产品类型和金额不能为空")

        # 生成订单号
        order_no = generate_order_no()

        # 创建订单
        order = Order(
            order_no=order_no,
            user_id=current_user.id,
            product_id=product_id,
            product_type=product_type,
            amount=amount,
            quantity=quantity,
            status=1,  # 待支付
            description=description,
        )
        db.add(order)
        await db.commit()

        logger.info(f"创建订单成功: {current_user.username} -> {order_no}")
        return success(
            {
                "id": order.id,
                "order_no": order.order_no,
                "amount": float(order.amount),
                "status": order.status,
                "status_text": order.status_text,
            },
            "创建订单成功",
        )

    except Exception as e:
        await db.rollback()
        logger.error(f"创建订单失败: {str(e)}")
        return error("创建订单失败")


@router.post("/{order_id}/pay", summary="订单支付")
async def pay_order(
    order_id: int,
    payment_method: str = Query(..., description="支付方式"),
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """订单支付"""
    try:
        result = await db.execute(
            select(Order).where(Order.id == order_id).options(selectinload(Order.user))
        )
        order = result.scalar_one_or_none()

        if not order:
            return not_found("订单不存在")

        # 检查权限（只能支付自己的订单）
        if order.user_id != current_user.id:
            return error("权限不足")

        # 检查是否可以支付
        if not order.can_pay():
            return error("订单状态不允许支付")

        # 检查用户余额（简化处理，实际项目中需要更复杂的支付逻辑）
        if current_user.member and float(current_user.member.balance) >= float(
            order.amount
        ):
            # 扣除用户余额
            success_deduct, new_balance = current_user.member.deduct_balance(
                float(order.amount)
            )
            if not success_deduct:
                return error("余额不足")

            # 更新订单状态
            order.status = 2  # 已支付
            order.payment_method = payment_method
            order.payment_time = datetime.now()

            # 创建点数交易记录（如果是点数充值）
            if order.product_type == "points":
                # 假设1元=10点数
                points = int(float(order.amount) * 10)
                current_user.member.add_points(points)

                transaction = PointTransaction(
                    user_id=current_user.id,
                    type=1,  # 充值
                    points=points,
                    balance_after=current_user.member.points,
                    amount=float(order.amount),
                    description=f"订单支付：{order.order_no}",
                    related_id=order.id,
                    related_type="order",
                )
                db.add(transaction)

            await db.commit()

            logger.info(f"订单支付成功: {current_user.username} -> {order.order_no}")
            return success(
                {
                    "order_id": order.id,
                    "order_no": order.order_no,
                    "status": order.status,
                    "status_text": order.status_text,
                    "payment_method": order.payment_method,
                    "payment_time": order.payment_time,
                },
                "支付成功",
            )
        else:
            return error("余额不足")

    except Exception as e:
        await db.rollback()
        logger.error(f"订单支付失败: {str(e)}")
        return error("支付失败")


@router.post("/{order_id}/cancel", summary="取消订单")
async def cancel_order(
    order_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """取消订单"""
    try:
        result = await db.execute(select(Order).where(Order.id == order_id))
        order = result.scalar_one_or_none()

        if not order:
            return not_found("订单不存在")

        # 检查权限（只能取消自己的订单，除非是管理员）
        if not current_user.is_admin and order.user_id != current_user.id:
            return error("权限不足")

        # 检查是否可以取消
        if not order.can_cancel():
            return error("订单状态不允许取消")

        # 更新订单状态
        order.status = 3  # 已取消

        await db.commit()

        logger.info(f"订单取消成功: {current_user.username} -> {order.order_no}")
        return success(
            {
                "order_id": order.id,
                "order_no": order.order_no,
                "status": order.status,
                "status_text": order.status_text,
            },
            "取消订单成功",
        )

    except Exception as e:
        await db.rollback()
        logger.error(f"订单取消失败: {str(e)}")
        return error("取消订单失败")


PRODUCTS = [
    {
        "id": 1,
        "name": "基础会员",
        "type": "member",
        "price": 99.00,
        "description": "基础会员服务，有效期1个月",
        "duration": 30,
        "points": 1000,
    },
    {
        "id": 2,
        "name": "高级会员",
        "type": "member",
        "price": 199.00,
        "description": "高级会员服务，有效期3个月",
        "duration": 90,
        "points": 3000,
    },
    {
        "id": 5,
        "name": "小额体验包",
        "type": "points",
        "price": 5.00,
        "description": "10点数体验包",
        "points": 10,
    },
    {
        "id": 6,
        "name": "15日套餐",
        "type": "subscription",
        "price": 15.00,
        "description": "时长套餐：15天",
        "duration": 15,
    },
    {
        "id": 7,
        "name": "月度套餐",
        "type": "subscription",
        "price": 25.00,
        "description": "时长套餐：30天",
        "duration": 30,
    },
    {
        "id": 8,
        "name": "季度套餐",
        "type": "subscription",
        "price": 50.00,
        "description": "时长套餐：90天",
        "duration": 90,
    },
    {
        "id": 9,
        "name": "半年套餐",
        "type": "subscription",
        "price": 80.00,
        "description": "时长套餐：180天",
        "duration": 180,
    },
    {
        "id": 10,
        "name": "年度套餐",
        "type": "subscription",
        "price": 120.00,
        "description": "时长套餐：365天",
        "duration": 365,
    },
]


@router.get("/products/list", summary="获取产品列表")
async def get_products(
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    try:
        return success(PRODUCTS, "获取产品列表成功")
    except Exception as e:
        logger.error(f"获取产品列表失败: {str(e)}")
        return error("获取产品列表失败")
