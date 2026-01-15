"""
角色权限模型
创建日期: 2025-01-08
用途: RBAC权限管理
"""

from typing import List, Optional
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Boolean,
    Text,
    ForeignKey,
    Table,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from config.database import Base


# 用户角色关联表
user_roles = Table(
    "user_roles",
    Base.metadata,
    Column(
        "user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    ),
    Column(
        "role_id", Integer, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True
    ),
)

# 角色权限关联表
role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column(
        "role_id", Integer, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True
    ),
    Column(
        "permission_id",
        Integer,
        ForeignKey("permissions.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class Role(Base):
    """角色表"""

    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False, index=True, comment="角色名称")
    description = Column(Text, nullable=True, comment="角色描述")
    is_system = Column(Boolean, default=False, nullable=False, comment="是否系统角色")
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # 关联关系
    users = relationship("User", secondary=user_roles, back_populates="roles")
    permissions = relationship(
        "Permission", secondary=role_permissions, back_populates="roles"
    )

    def __repr__(self):
        return f"<Role(id={self.id}, name='{self.name}')>"

    def has_permission(self, permission_code: str) -> bool:
        """检查是否有指定权限"""
        return any(p.code == permission_code for p in self.permissions)

    def add_permission(self, permission):
        """添加权限"""
        if permission not in self.permissions:
            self.permissions.append(permission)

    def remove_permission(self, permission):
        """移除权限"""
        if permission in self.permissions:
            self.permissions.remove(permission)


class Permission(Base):
    """权限表"""

    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False, comment="权限名称")
    code = Column(String(100), unique=True, nullable=False, index=True, comment="权限代码")
    resource = Column(String(50), nullable=False, comment="资源类型")
    action = Column(String(50), nullable=False, comment="操作类型")
    description = Column(Text, nullable=True, comment="权限描述")
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # 关联关系
    roles = relationship(
        "Role", secondary=role_permissions, back_populates="permissions"
    )
    menus = relationship("Menu", back_populates="permission")

    def __repr__(self):
        return f"<Permission(id={self.id}, code='{self.code}', name='{self.name}')>"

    @property
    def full_code(self) -> str:
        """完整权限代码"""
        return f"{self.resource}:{self.action}"


# 为用户模型添加角色关联（需要在User模型中定义）
def init_user_role_relationship():
    """初始化用户角色关系"""
    from .user import User

    User.roles = relationship("Role", secondary=user_roles, back_populates="users")
