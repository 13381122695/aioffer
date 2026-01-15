#!/usr/bin/env python3
"""
数据库测试脚本
创建日期: 2025-01-08
用途: 测试数据库连接和创建初始数据
"""

import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from config.database import get_async_session, init_db, async_engine
from models.user import User, UserAuth
from models.role import Role, Permission
from utils.security import SecurityManager


async def create_test_data():
    """创建测试数据"""
    # 初始化数据库表
    print("正在初始化数据库表...")
    await init_db()
    print("数据库表初始化完成")

    async for db in get_async_session():
        try:
            # 检查是否已有管理员用户
            result = await db.execute(select(User).where(User.username == "admin"))
            admin_user = result.scalar_one_or_none()

            if not admin_user:
                # 创建管理员用户
                admin_user = User(
                    username="admin",
                    email="admin@example.com",
                    password_hash=SecurityManager.hash_password("123456"),
                    full_name="管理员",
                    status=1,
                    user_type=3,  # 管理员
                )
                db.add(admin_user)
                await db.flush()

                # 创建用户认证记录
                user_auth = UserAuth(
                    user_id=admin_user.id,
                    auth_type="email",
                    auth_key="admin@example.com",
                    auth_secret=admin_user.password_hash,
                    is_verified=True,
                )
                db.add(user_auth)

                print("管理员用户创建成功")
            else:
                print("管理员用户已存在")

            # 创建测试角色
            result = await db.execute(select(Role).where(Role.name == "管理员"))
            admin_role = result.scalar_one_or_none()

            if not admin_role:
                admin_role = Role(name="管理员", description="系统管理员角色", is_system=True)
                db.add(admin_role)
                await db.flush()
                print("管理员角色创建成功")

            # 创建测试权限
            permissions = [
                ("查看用户", "user:read", "查看用户"),
                ("创建用户", "user:create", "创建用户"),
                ("更新用户", "user:update", "更新用户"),
                ("删除用户", "user:delete", "删除用户"),
                ("查看系统", "system:read", "查看系统信息"),
            ]

            for name, code, description in permissions:
                result = await db.execute(
                    select(Permission).where(Permission.code == code)
                )
                permission = result.scalar_one_or_none()

                if not permission:
                    permission = Permission(
                        name=name,
                        code=code,
                        resource=code.split(":")[0],
                        action=code.split(":")[1],
                        description=description,
                    )
                    db.add(permission)
                    print(f"权限 {code} 创建成功")

            await db.commit()
            print("测试数据创建完成")

        except Exception as e:
            await db.rollback()
            print(f"创建测试数据失败: {str(e)}")
            raise
        finally:
            await db.close()

    # 关闭数据库连接池
    await async_engine.dispose()


if __name__ == "__main__":
    from sqlalchemy import select

    asyncio.run(create_test_data())
