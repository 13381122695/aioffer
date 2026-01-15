"""
用户管理路由
创建日期: 2025-01-08
用途: 用户管理相关功能
"""

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import selectinload

from config import get_async_session
from models import User, UserAuth, Member
from schemas import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserListResponse,
    RechargeRequest,
)
from utils.security import SecurityManager
from utils.response import success, error, not_found, paginated
from utils.logger import get_logger
from routers.auth import get_current_user

logger = get_logger(__name__)
router = APIRouter()


@router.get("/", summary="获取用户列表")
async def get_users(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=1, le=100, description="每页数量"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    status: Optional[int] = Query(None, ge=1, le=3, description="用户状态"),
    user_type: Optional[int] = Query(None, ge=1, le=3, description="用户类型"),
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """获取用户列表"""
    try:
        if not current_user.is_admin:
            query = select(User).where(User.id == current_user.id)
        else:
            query = select(User)

        # 应用筛选条件
        if current_user.is_admin and search:
            query = query.where(
                or_(
                    User.username.contains(search),
                    User.email.contains(search),
                    User.full_name.contains(search),
                    User.phone.contains(search),
                )
            )

        if current_user.is_admin and status is not None:
            query = query.where(User.status == status)

        if current_user.is_admin and user_type is not None:
            query = query.where(User.user_type == user_type)

        # 计算总数
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # 分页查询
        offset = (page - 1) * size
        query = query.offset(offset).limit(size)

        result = await db.execute(query)
        users = result.scalars().all()

        # 转换为用户响应模式
        user_responses = []
        for user in users:
            user_responses.append(UserResponse.model_validate(user))

        return paginated(user_responses, total, page, size, "获取用户列表成功")

    except Exception as e:
        logger.error(f"获取用户列表失败: {str(e)}")
        return error("获取用户列表失败")


@router.get("/stats", summary="获取用户统计")
async def get_user_stats(
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """获取用户统计数据"""
    try:
        # 总用户数
        total_query = select(func.count(User.id))
        total_result = await db.execute(total_query)
        total_users = total_result.scalar() or 0

        # 活跃用户数
        active_query = select(func.count(User.id)).where(User.status == 1)
        active_result = await db.execute(active_query)
        active_users = active_result.scalar() or 0

        # 今日新增
        today = datetime.now().date()
        new_query = select(func.count(User.id)).where(
            func.date(User.created_at) == today
        )
        new_result = await db.execute(new_query)
        new_users_today = new_result.scalar() or 0

        # 总点数
        points_query = select(func.sum(Member.points))
        points_result = await db.execute(points_query)
        total_points = points_result.scalar() or 0

        return success(
            {
                "total_users": total_users,
                "active_users": active_users,
                "new_users_today": new_users_today,
                "total_points": total_points,
            },
            "获取统计数据成功",
        )
    except Exception as e:
        logger.error(f"获取用户统计失败: {str(e)}")
        return error("获取统计数据失败")


@router.get("/transactions", summary="获取所有交易记录")
async def get_all_transactions(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=1, le=100, description="每页数量"),
    user_id: Optional[int] = Query(None, description="用户ID"),
    type: Optional[int] = Query(None, description="交易类型"),
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """获取所有交易记录"""
    try:
        if not current_user.is_admin:
            return error("权限不足")

        from models import PointTransaction

        query = (
            select(PointTransaction, User.username)
            .outerjoin(User, User.id == PointTransaction.user_id)
            .order_by(PointTransaction.created_at.desc())
        )

        if user_id:
            query = query.where(PointTransaction.user_id == user_id)
        if type:
            query = query.where(PointTransaction.type == type)

        # 计算总数
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # 分页
        offset = (page - 1) * size
        query = query.offset(offset).limit(size)

        result = await db.execute(query)
        rows = result.all()

        # 转换数据
        transaction_data = []
        for transaction, username in rows:
            transaction_data.append(
                {
                    "id": transaction.id,
                    "user_id": transaction.user_id,
                    "username": username,
                    "type": transaction.type,
                    "type_text": transaction.type_text,
                    "points": transaction.points,
                    "balance_after": transaction.balance_after,
                    "amount": float(transaction.amount) if transaction.amount else None,
                    "description": transaction.description,
                    "created_at": transaction.created_at,
                }
            )

        return paginated(transaction_data, total, page, size, "获取交易记录成功")

    except Exception as e:
        logger.error(f"获取交易记录失败: {str(e)}")
        return error("获取交易记录失败")


@router.get("/{user_id}", summary="获取用户详情")
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """获取用户详情"""
    try:
        if not current_user.is_admin and user_id != current_user.id:
            return error("权限不足")

        result = await db.execute(
            select(User)
            .where(User.id == user_id)
            .options(selectinload(User.auths), selectinload(User.member))
        )
        user = result.scalar_one_or_none()

        if not user:
            return not_found("用户不存在")

        user_data = UserResponse.model_validate(user)

        # 添加额外信息
        user_dict = user_data.model_dump()
        user_dict["auths"] = [auth.to_dict() for auth in user.auths]
        if user.member:
            user_dict["member"] = {
                "id": user.member.id,
                "member_level": user.member.member_level,
                "points": user.member.points,
                "balance": float(user.member.balance),
                "expired_at": user.member.expired_at,
                "is_expired": user.member.is_expired,
                "is_valid_member": user.member.is_valid_member,
            }

        return success(user_dict, "获取用户详情成功")

    except Exception as e:
        logger.error(f"获取用户详情失败: {str(e)}")
        return error("获取用户详情失败")


@router.post("/", summary="创建用户")
async def create_user(
    request: UserCreate,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """创建用户"""
    try:
        # 检查权限（只有管理员可以创建用户）
        if not current_user.is_admin:
            return error("权限不足")

        # 检查用户名是否已存在
        result = await db.execute(select(User).where(User.username == request.username))
        if result.scalar_one_or_none():
            return error("用户名已存在")

        # 检查邮箱是否已存在（如果提供了邮箱）
        if request.email:
            result = await db.execute(select(User).where(User.email == request.email))
            if result.scalar_one_or_none():
                return error("邮箱已存在")

        # 创建用户
        user_data = request.model_dump()

        # 处理前端兼容字段
        role = user_data.pop("role", None)
        if role is not None:
            user_data["user_type"] = role

        is_active = user_data.pop("is_active", None)
        if is_active is not None:
            user_data["status"] = 1 if is_active else 2

        password = user_data.pop("password", None)
        if password:
            user_data["password_hash"] = SecurityManager.hash_password(password)

        user = User(**user_data)
        db.add(user)
        await db.flush()

        # 创建用户认证记录
        if request.email:
            user_auth = UserAuth(
                user_id=user.id,
                auth_type="email",
                auth_key=request.email,
                auth_secret=user.password_hash,
                is_verified=True,
                verified_at=datetime.now(),
            )
            db.add(user_auth)

        await db.commit()
        await db.refresh(user)

        logger.info(f"管理员创建用户成功: {current_user.username} -> {user.username}")
        return success(UserResponse.model_validate(user), "创建用户成功")

    except Exception as e:
        await db.rollback()
        logger.error(f"创建用户失败: {str(e)}")
        return error("创建用户失败")


@router.put("/{user_id}", summary="更新用户")
async def update_user(
    user_id: int,
    request: UserUpdate,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """更新用户"""
    try:
        # 检查权限（只有管理员可以更新其他用户）
        if user_id != current_user.id and not current_user.is_admin:
            return error("权限不足")

        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            return not_found("用户不存在")

        # 更新用户字段
        update_data = request.model_dump(exclude_unset=True)

        # 处理前端兼容字段
        role = update_data.pop("role", None) if "role" in update_data else None
        if role is not None:
            update_data["user_type"] = role

        if "is_active" in update_data:
            is_active = update_data.pop("is_active")
            if is_active is not None:
                update_data["status"] = 1 if is_active else 2

        # 如果更新密码，需要重新哈希
        if "password" in update_data and update_data["password"]:
            update_data["password_hash"] = SecurityManager.hash_password(
                update_data.pop("password")
            )

        for field, value in update_data.items():
            setattr(user, field, value)

        await db.commit()
        await db.refresh(user)

        logger.info(f"用户更新成功: {current_user.username} -> {user.username}")
        return success(UserResponse.model_validate(user), "更新用户成功")

    except Exception as e:
        await db.rollback()
        logger.error(f"更新用户失败: {str(e)}")
        return error("更新用户失败")


@router.delete("/{user_id}", summary="删除用户")
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """删除用户"""
    try:
        # 检查权限（只有管理员可以删除用户）
        if not current_user.is_admin:
            return error("权限不足")

        # 不能删除自己
        if user_id == current_user.id:
            return error("不能删除自己的账号")

        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            return not_found("用户不存在")

        # 软删除，将状态设置为已删除
        user.status = 3
        await db.commit()

        logger.info(f"用户删除成功: {current_user.username} -> {user.username}")
        return success(None, "删除用户成功")

    except Exception as e:
        await db.rollback()
        logger.error(f"删除用户失败: {str(e)}")
        return error("删除用户失败")


@router.get("/{user_id}/points", summary="获取用户点数记录")
async def get_user_points(
    user_id: int,
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=1, le=100, description="每页数量"),
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """获取用户点数记录"""
    try:
        # 检查权限（只能查看自己的记录，除非是管理员）
        if user_id != current_user.id and not current_user.is_admin:
            return error("权限不足")

        from models import PointTransaction

        # 查询点数记录
        query = (
            select(PointTransaction)
            .where(PointTransaction.user_id == user_id)
            .order_by(PointTransaction.created_at.desc())
        )

        # 计算总数
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # 分页查询
        offset = (page - 1) * size
        query = query.offset(offset).limit(size)

        result = await db.execute(query)
        transactions = result.scalars().all()

        # 转换为响应格式
        transaction_data = []
        for transaction in transactions:
            transaction_data.append(
                {
                    "id": transaction.id,
                    "type": transaction.type,
                    "type_text": transaction.type_text,
                    "points": transaction.points,
                    "balance_after": transaction.balance_after,
                    "amount": float(transaction.amount) if transaction.amount else None,
                    "description": transaction.description,
                    "related_id": transaction.related_id,
                    "related_type": transaction.related_type,
                    "created_at": transaction.created_at,
                }
            )

        return paginated(transaction_data, total, page, size, "获取点数记录成功")

    except Exception as e:
        logger.error(f"获取用户点数记录失败: {str(e)}")
        return error("获取点数记录失败")


@router.post("/recharge-points", summary="用户充值")
async def recharge_points(
    request: RechargeRequest,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """用户充值"""
    try:
        # 检查权限（只有管理员可以为用户充值）
        if not current_user.is_admin:
            return error("权限不足")

        user_id = request.user_id
        points = request.points
        amount = request.amount

        result = await db.execute(
            select(User).where(User.id == user_id).options(selectinload(User.member))
        )
        user = result.scalar_one_or_none()

        if not user:
            return not_found("用户不存在")

        # 如果没有会员记录，创建会员记录
        if not user.member:
            member = Member(user_id=user.id, points=0, balance=0.00)
            db.add(member)
            await db.flush()
            user.member = member

        # 增加点数和余额
        user.member.add_points(points)
        user.member.add_balance(amount)

        # 创建点数交易记录
        from models import PointTransaction

        transaction = PointTransaction(
            user_id=user.id,
            type=1,  # 充值
            points=points,
            balance_after=user.member.points,
            amount=amount,
            description=request.description or f"管理员充值：{points}点数",
        )
        db.add(transaction)

        await db.commit()

        logger.info(f"用户充值成功: {current_user.username} -> {user.username}, 点数: {points}")
        return success(
            {
                "user_id": user.id,
                "username": user.username,
                "points": user.member.points,
                "balance": float(user.member.balance),
                "recharge_points": points,
                "recharge_amount": amount,
            },
            "充值成功",
        )

    except Exception as e:
        await db.rollback()
        logger.error(f"用户充值失败: {str(e)}")
        return error("充值失败")
