"""
菜单模型
创建日期: 2025-01-08
用途: 动态菜单管理
"""

from typing import Optional, List
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from config.database import Base


class Menu(Base):
    """菜单表"""

    __tablename__ = "menus"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(50), nullable=False, comment="菜单名称")
    path = Column(String(100), nullable=True, comment="菜单路径")
    component = Column(String(100), nullable=True, comment="组件名称")
    icon = Column(String(50), nullable=True, comment="图标")
    parent_id = Column(
        Integer,
        ForeignKey("menus.id", ondelete="CASCADE"),
        nullable=True,
        comment="父菜单ID",
    )
    sort_order = Column(Integer, default=0, nullable=False, comment="排序")
    is_visible = Column(Boolean, default=True, nullable=False, comment="是否可见")
    permission_id = Column(
        Integer,
        ForeignKey("permissions.id", ondelete="SET NULL"),
        nullable=True,
        comment="关联权限ID",
    )
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # 关联关系
    parent = relationship("Menu", remote_side=[id], back_populates="children")
    children = relationship(
        "Menu", back_populates="parent", cascade="all, delete-orphan"
    )
    permission = relationship("Permission", back_populates="menus")

    def __repr__(self):
        return f"<Menu(id={self.id}, name='{self.name}', path='{self.path}')>"

    @property
    def is_parent(self) -> bool:
        """是否为父菜单"""
        return len(self.children) > 0

    @property
    def is_leaf(self) -> bool:
        """是否为叶子菜单"""
        return len(self.children) == 0

    def to_dict(self, include_children: bool = True) -> dict:
        """转换为字典"""
        data = {
            "id": self.id,
            "name": self.name,
            "path": self.path,
            "component": self.component,
            "icon": self.icon,
            "parent_id": self.parent_id,
            "sort_order": self.sort_order,
            "is_visible": self.is_visible,
            "permission_id": self.permission_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

        if include_children and self.children:
            data["children"] = [
                child.to_dict()
                for child in sorted(self.children, key=lambda x: x.sort_order)
            ]

        return data
