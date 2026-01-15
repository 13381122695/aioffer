"""
菜单管理路由
创建日期: 2025-01-08
用途: 动态菜单管理功能
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload

from config import get_async_session
from models import User, Menu, Permission
from utils.response import success, error, not_found, paginated
from utils.logger import get_logger
from routers.auth import get_current_user

logger = get_logger(__name__)
router = APIRouter()


@router.get("/", summary="获取菜单树")
async def get_menus(
    parent_id: Optional[int] = Query(None, description="父菜单ID"),
    is_visible: Optional[bool] = Query(None, description="是否可见"),
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """获取菜单树"""
    try:
        # 构建查询
        query = select(Menu).options(selectinload(Menu.children))

        # 应用筛选条件
        if parent_id is not None:
            query = query.where(Menu.parent_id == parent_id)

        if is_visible is not None:
            query = query.where(Menu.is_visible == is_visible)

        # 按排序字段排序
        query = query.order_by(Menu.sort_order, Menu.id)

        result = await db.execute(query)
        menus = result.scalars().all()

        # 构建菜单树
        menu_tree = []
        for menu in menus:
            # 只获取顶级菜单（parent_id为None）
            if menu.parent_id is None:
                menu_data = menu.to_dict()
                menu_tree.append(menu_data)

        return success(menu_tree, "获取菜单树成功")

    except Exception as e:
        logger.error(f"获取菜单树失败: {str(e)}")
        return error("获取菜单树失败")


@router.get("/user", summary="获取用户菜单")
async def get_user_menus(
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """获取用户菜单"""
    try:
        # 获取用户权限代码列表
        user_permissions = set()

        # 获取用户角色
        from models import user_roles

        result = await db.execute(
            select(user_roles.c.role_id).where(user_roles.c.user_id == current_user.id)
        )
        role_ids = [row[0] for row in result.fetchall()]

        if role_ids:
            # 获取角色权限
            from models import role_permissions

            result = await db.execute(
                select(role_permissions.c.permission_id).where(
                    role_permissions.c.role_id.in_(role_ids)
                )
            )
            permission_ids = [row[0] for row in result.fetchall()]

            if permission_ids:
                # 获取权限代码
                result = await db.execute(
                    select(Permission.code).where(Permission.id.in_(permission_ids))
                )
                user_permissions.update([row[0] for row in result.fetchall()])

        # 获取所有可见菜单（预加载 permission，避免访问关系时触发懒加载 IO）
        query = (
            select(Menu)
            .where(Menu.is_visible == True)
            .options(selectinload(Menu.permission))
            .order_by(Menu.sort_order, Menu.id)
        )
        result = await db.execute(query)
        all_menus = result.scalars().all()

        # 过滤用户有权限的菜单
        user_menus = []
        for menu in all_menus:
            # 如果没有关联权限，或者用户有该权限，则显示菜单
            if not menu.permission_id or (
                menu.permission and menu.permission.code in user_permissions
            ):
                menu_data = menu.to_dict(include_children=False)
                user_menus.append(menu_data)

        # 构建菜单树
        menu_tree = []
        menu_dict = {menu["id"]: menu for menu in user_menus}

        for menu in user_menus:
            if menu["parent_id"] is None:
                menu_tree.append(menu)
            else:
                parent = menu_dict.get(menu["parent_id"])
                if parent:
                    if "children" not in parent:
                        parent["children"] = []
                    parent["children"].append(menu)

        if current_user.is_member and not current_user.is_admin:
            allowed_names = {"会员管理", "外部系统"}
            allowed_paths = {"/members", "/external-systems"}
            menu_tree = [
                m
                for m in menu_tree
                if m.get("name") in allowed_names or m.get("path") in allowed_paths
            ]

        return success(menu_tree, "获取用户菜单成功")

    except Exception as e:
        logger.error(f"获取用户菜单失败: {str(e)}")
        return error("获取用户菜单失败")


@router.get("/{menu_id}", summary="获取菜单详情")
async def get_menu(
    menu_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """获取菜单详情"""
    try:
        # 检查权限（只有管理员可以查看菜单详情）
        if not current_user.is_admin:
            return error("权限不足")

        result = await db.execute(
            select(Menu)
            .where(Menu.id == menu_id)
            .options(selectinload(Menu.permission))
        )
        menu = result.scalar_one_or_none()

        if not menu:
            return not_found("菜单不存在")

        menu_data = menu.to_dict(include_children=False)

        # 添加权限信息
        if menu.permission:
            menu_data["permission"] = {
                "id": menu.permission.id,
                "name": menu.permission.name,
                "code": menu.permission.code,
                "resource": menu.permission.resource,
                "action": menu.permission.action,
            }

        return success(menu_data, "获取菜单详情成功")

    except Exception as e:
        logger.error(f"获取菜单详情失败: {str(e)}")
        return error("获取菜单详情失败")


@router.post("/", summary="创建菜单")
async def create_menu(
    request: dict,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """创建菜单"""
    try:
        # 检查权限（只有管理员可以创建菜单）
        if not current_user.is_admin:
            return error("权限不足")

        name = request.get("name")
        path = request.get("path")
        component = request.get("component")
        icon = request.get("icon")
        parent_id = request.get("parent_id")
        sort_order = request.get("sort_order", 0)
        is_visible = request.get("is_visible", True)
        permission_id = request.get("permission_id")

        if not name:
            return error("菜单名称不能为空")

        # 检查父菜单是否存在
        if parent_id:
            result = await db.execute(select(Menu).where(Menu.id == parent_id))
            if not result.scalar_one_or_none():
                return error("父菜单不存在")

        # 检查权限是否存在（如果指定了权限）
        if permission_id:
            result = await db.execute(
                select(Permission).where(Permission.id == permission_id)
            )
            if not result.scalar_one_or_none():
                return error("权限不存在")

        # 创建菜单
        menu = Menu(
            name=name,
            path=path,
            component=component,
            icon=icon,
            parent_id=parent_id,
            sort_order=sort_order,
            is_visible=is_visible,
            permission_id=permission_id,
        )
        db.add(menu)
        await db.commit()
        await db.refresh(menu)

        menu_data = menu.to_dict(include_children=False)
        logger.info(f"创建菜单成功: {current_user.username} -> {menu.name}")
        return success(menu_data, "创建菜单成功")

    except Exception as e:
        await db.rollback()
        logger.error(f"创建菜单失败: {str(e)}")
        return error("创建菜单失败")


@router.put("/{menu_id}", summary="更新菜单")
async def update_menu(
    menu_id: int,
    request: dict,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """更新菜单"""
    try:
        # 检查权限（只有管理员可以更新菜单）
        if not current_user.is_admin:
            return error("权限不足")

        result = await db.execute(select(Menu).where(Menu.id == menu_id))
        menu = result.scalar_one_or_none()

        if not menu:
            return not_found("菜单不存在")

        # 更新菜单字段
        allowed_fields = [
            "name",
            "path",
            "component",
            "icon",
            "parent_id",
            "sort_order",
            "is_visible",
            "permission_id",
        ]

        for field in allowed_fields:
            if field in request and request[field] is not None:
                # 特殊处理parent_id
                if field == "parent_id":
                    parent_id = request[field]
                    if parent_id is not None:
                        # 检查父菜单是否存在
                        result = await db.execute(
                            select(Menu).where(Menu.id == parent_id)
                        )
                        if not result.scalar_one_or_none():
                            return error("父菜单不存在")
                        # 检查是否会导致循环引用
                        if parent_id == menu_id:
                            return error("不能将菜单设置为自己的子菜单")

                # 特殊处理permission_id
                if field == "permission_id":
                    permission_id = request[field]
                    if permission_id is not None:
                        # 检查权限是否存在
                        result = await db.execute(
                            select(Permission).where(Permission.id == permission_id)
                        )
                        if not result.scalar_one_or_none():
                            return error("权限不存在")

                setattr(menu, field, request[field])

        await db.commit()
        await db.refresh(menu)

        menu_data = menu.to_dict(include_children=False)
        logger.info(f"更新菜单成功: {current_user.username} -> {menu.name}")
        return success(menu_data, "更新菜单成功")

    except Exception as e:
        await db.rollback()
        logger.error(f"更新菜单失败: {str(e)}")
        return error("更新菜单失败")


@router.delete("/{menu_id}", summary="删除菜单")
async def delete_menu(
    menu_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """删除菜单"""
    try:
        # 检查权限（只有管理员可以删除菜单）
        if not current_user.is_admin:
            return error("权限不足")

        result = await db.execute(select(Menu).where(Menu.id == menu_id))
        menu = result.scalar_one_or_none()

        if not menu:
            return not_found("菜单不存在")

        # 检查是否有子菜单
        result = await db.execute(select(Menu).where(Menu.parent_id == menu_id))
        if result.scalar_one_or_none():
            return error("该菜单存在子菜单，无法删除")

        # 删除菜单
        await db.delete(menu)
        await db.commit()

        logger.info(f"删除菜单成功: {current_user.username} -> {menu.name}")
        return success(None, "删除菜单成功")

    except Exception as e:
        await db.rollback()
        logger.error(f"删除菜单失败: {str(e)}")
        return error("删除菜单失败")
