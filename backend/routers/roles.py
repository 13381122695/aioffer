"""
角色权限管理路由
创建日期: 2025-01-08
用途: 角色和权限管理功能
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import selectinload

from config import get_async_session
from models import User, Role, Permission, user_roles, role_permissions
from schemas import RoleCreate, RoleUpdate, RoleResponse, PermissionResponse
from utils.response import success, error, not_found, paginated
from utils.logger import get_logger
from routers.auth import get_current_user

logger = get_logger(__name__)
router = APIRouter()


@router.get("/", summary="获取角色列表")
async def get_roles(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=1, le=100, description="每页数量"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """获取角色列表"""
    try:
        # 检查权限（只有管理员可以查看角色）
        if not current_user.is_admin:
            return error("权限不足")

        # 构建查询
        query = select(Role).options(selectinload(Role.permissions))

        # 应用筛选条件
        if search:
            query = query.where(
                or_(Role.name.contains(search), Role.description.contains(search))
            )

        # 计算总数
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0

        # 分页查询
        offset = (page - 1) * size
        query = query.offset(offset).limit(size)

        result = await db.execute(query)
        roles = result.scalars().all()

        # 转换为角色响应模式
        role_responses = []
        for role in roles:
            role_data = {
                "id": role.id,
                "name": role.name,
                "description": role.description,
                "is_system": role.is_system,
                "created_at": role.created_at,
                "permission_count": len(role.permissions),
            }
            role_responses.append(role_data)

        return paginated(role_responses, total, page, size, "获取角色列表成功")

    except Exception as e:
        logger.error(f"获取角色列表失败: {str(e)}")
        return error("获取角色列表失败")


@router.get("/permissions/all", summary="获取所有权限")
async def get_all_permissions(
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """获取所有权限"""
    try:
        if not current_user.is_admin:
            return error("权限不足")

        result = await db.execute(select(Permission).order_by(Permission.id.asc()))
        permissions = result.scalars().all()

        permission_data = []
        for p in permissions:
            permission_data.append(
                {
                    "id": p.id,
                    "name": p.name,
                    "code": p.code,
                    "resource": p.resource,
                    "action": p.action,
                    "description": p.description,
                    "full_code": p.full_code,
                }
            )

        return success(permission_data, "获取权限列表成功")
    except Exception as e:
        logger.error(f"获取权限列表失败: {str(e)}")
        return error("获取权限列表失败")


@router.get("/{role_id}", summary="获取角色详情")
async def get_role(
    role_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """获取角色详情"""
    try:
        # 检查权限（只有管理员可以查看角色）
        if not current_user.is_admin:
            return error("权限不足")

        result = await db.execute(
            select(Role)
            .where(Role.id == role_id)
            .options(selectinload(Role.permissions))
        )
        role = result.scalar_one_or_none()

        if not role:
            return not_found("角色不存在")

        # 转换为角色响应模式
        role_data = {
            "id": role.id,
            "name": role.name,
            "description": role.description,
            "is_system": role.is_system,
            "created_at": role.created_at,
            "permissions": [
                {
                    "id": p.id,
                    "name": p.name,
                    "code": p.code,
                    "resource": p.resource,
                    "action": p.action,
                    "description": p.description,
                }
                for p in role.permissions
            ],
        }

        return success(role_data, "获取角色详情成功")

    except Exception as e:
        logger.error(f"获取角色详情失败: {str(e)}")
        return error("获取角色详情失败")


@router.post("/", summary="创建角色")
async def create_role(
    request: dict,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """创建角色"""
    try:
        # 检查权限（只有管理员可以创建角色）
        if not current_user.is_admin:
            return error("权限不足")

        name = request.get("name")
        description = request.get("description")
        permission_ids = request.get("permission_ids", [])

        if not name:
            return error("角色名称不能为空")

        # 检查角色名称是否已存在
        result = await db.execute(select(Role).where(Role.name == name))
        if result.scalar_one_or_none():
            return error("角色名称已存在")

        # 创建角色
        role = Role(name=name, description=description)
        db.add(role)
        await db.flush()

        # 分配权限
        if permission_ids:
            permissions_result = await db.execute(
                select(Permission).where(Permission.id.in_(permission_ids))
            )
            permissions = permissions_result.scalars().all()
            role.permissions.extend(permissions)

        await db.commit()

        logger.info(f"创建角色成功: {current_user.username} -> {role.name}")
        return success(
            {
                "id": role.id,
                "name": role.name,
                "description": role.description,
                "permission_count": len(role.permissions),
            },
            "创建角色成功",
        )

    except Exception as e:
        await db.rollback()
        logger.error(f"创建角色失败: {str(e)}")
        return error("创建角色失败")


@router.put("/{role_id}", summary="更新角色")
async def update_role(
    role_id: int,
    request: dict,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """更新角色"""
    try:
        # 检查权限（只有管理员可以更新角色）
        if not current_user.is_admin:
            return error("权限不足")

        result = await db.execute(
            select(Role)
            .where(Role.id == role_id)
            .options(selectinload(Role.permissions))
        )
        role = result.scalar_one_or_none()

        if not role:
            return not_found("角色不存在")

        # 系统角色不允许修改
        if role.is_system:
            return error("系统角色不允许修改")

        # 更新角色信息
        name = request.get("name")
        description = request.get("description")
        permission_ids = request.get("permission_ids")

        if name and name != role.name:
            # 检查新名称是否已存在
            result = await db.execute(select(Role).where(Role.name == name))
            if result.scalar_one_or_none():
                return error("角色名称已存在")
            role.name = name

        if description is not None:
            role.description = description

        # 更新权限
        if permission_ids is not None:
            # 清空现有权限
            role.permissions.clear()

            # 添加新权限
            if permission_ids:
                permissions_result = await db.execute(
                    select(Permission).where(Permission.id.in_(permission_ids))
                )
                permissions = permissions_result.scalars().all()
                role.permissions.extend(permissions)

        await db.commit()

        logger.info(f"更新角色成功: {current_user.username} -> {role.name}")
        return success(
            {
                "id": role.id,
                "name": role.name,
                "description": role.description,
                "permission_count": len(role.permissions),
            },
            "更新角色成功",
        )

    except Exception as e:
        await db.rollback()
        logger.error(f"更新角色失败: {str(e)}")
        return error("更新角色失败")


@router.delete("/{role_id}", summary="删除角色")
async def delete_role(
    role_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """删除角色"""
    try:
        # 检查权限（只有管理员可以删除角色）
        if not current_user.is_admin:
            return error("权限不足")

        result = await db.execute(select(Role).where(Role.id == role_id))
        role = result.scalar_one_or_none()

        if not role:
            return not_found("角色不存在")

        # 系统角色不允许删除
        if role.is_system:
            return error("系统角色不允许删除")

        # 检查是否有用户在使用该角色
        user_count_result = await db.execute(
            select(user_roles).where(user_roles.c.role_id == role_id)
        )
        if user_count_result.scalar_one_or_none():
            return error("该角色正在被用户使用，无法删除")

        # 删除角色
        await db.delete(role)
        await db.commit()

        logger.info(f"删除角色成功: {current_user.username} -> {role.name}")
        return success(None, "删除角色成功")

    except Exception as e:
        await db.rollback()
        logger.error(f"删除角色失败: {str(e)}")
        return error("删除角色失败")


@router.get("/{role_id}/permissions", summary="获取角色权限")
async def get_role_permissions(
    role_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """获取角色权限"""
    try:
        # 检查权限（只有管理员可以查看角色权限）
        if not current_user.is_admin:
            return error("权限不足")

        result = await db.execute(
            select(Role)
            .where(Role.id == role_id)
            .options(selectinload(Role.permissions))
        )
        role = result.scalar_one_or_none()

        if not role:
            return not_found("角色不存在")

        permissions = []
        for permission in role.permissions:
            permissions.append(
                {
                    "id": permission.id,
                    "name": permission.name,
                    "code": permission.code,
                    "resource": permission.resource,
                    "action": permission.action,
                    "description": permission.description,
                }
            )

        return success(permissions, "获取角色权限成功")

    except Exception as e:
        logger.error(f"获取角色权限失败: {str(e)}")
        return error("获取角色权限失败")


@router.post("/{role_id}/permissions", summary="分配角色权限")
async def assign_role_permissions(
    role_id: int,
    request: dict,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """分配角色权限"""
    try:
        # 检查权限（只有管理员可以分配角色权限）
        if not current_user.is_admin:
            return error("权限不足")

        permission_ids = request.get("permission_ids", [])

        result = await db.execute(
            select(Role)
            .where(Role.id == role_id)
            .options(selectinload(Role.permissions))
        )
        role = result.scalar_one_or_none()

        if not role:
            return not_found("角色不存在")

        # 系统角色不允许修改权限
        if role.is_system:
            return error("系统角色不允许修改权限")

        # 清空现有权限
        role.permissions.clear()

        # 添加新权限
        if permission_ids:
            permissions_result = await db.execute(
                select(Permission).where(Permission.id.in_(permission_ids))
            )
            permissions = permissions_result.scalars().all()
            role.permissions.extend(permissions)

        await db.commit()

        logger.info(f"分配角色权限成功: {current_user.username} -> {role.name}")
        return success(
            {"role_id": role.id, "permission_count": len(role.permissions)}, "分配角色权限成功"
        )

    except Exception as e:
        await db.rollback()
        logger.error(f"分配角色权限失败: {str(e)}")
        return error("分配角色权限失败")
