"""
菜单相关Pydantic模型
创建日期: 2025-01-08
用途: 菜单管理的数据验证
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class MenuBase(BaseModel):
    """菜单基础模型"""

    name: str = Field(..., min_length=1, max_length=50, description="菜单名称")
    path: Optional[str] = Field(None, max_length=100, description="菜单路径")
    component: Optional[str] = Field(None, max_length=100, description="组件名称")
    icon: Optional[str] = Field(None, max_length=50, description="图标")
    parent_id: Optional[int] = Field(None, description="父菜单ID")
    sort_order: int = Field(default=0, description="排序")
    is_visible: bool = Field(default=True, description="是否可见")
    permission_id: Optional[int] = Field(None, description="关联权限ID")


class MenuCreate(MenuBase):
    """创建菜单模型"""

    pass


class MenuUpdate(BaseModel):
    """更新菜单模型"""

    name: Optional[str] = Field(None, min_length=1, max_length=50, description="菜单名称")
    path: Optional[str] = Field(None, max_length=100, description="菜单路径")
    component: Optional[str] = Field(None, max_length=100, description="组件名称")
    icon: Optional[str] = Field(None, max_length=50, description="图标")
    parent_id: Optional[int] = Field(None, description="父菜单ID")
    sort_order: Optional[int] = Field(None, description="排序")
    is_visible: Optional[bool] = Field(None, description="是否可见")
    permission_id: Optional[int] = Field(None, description="关联权限ID")


class MenuResponse(MenuBase):
    """菜单响应模型"""

    id: int = Field(..., description="菜单ID")
    created_at: datetime = Field(..., description="创建时间")
    children: List["MenuResponse"] = Field(default_factory=list, description="子菜单")

    class Config:
        from_attributes = True


class MenuList(BaseModel):
    """菜单列表响应模型"""

    items: List[MenuResponse] = Field(..., description="菜单列表")
    total: int = Field(..., description="总数")
    page: int = Field(..., description="当前页码")
    size: int = Field(..., description="每页数量")


class MenuTree(BaseModel):
    """菜单树形结构模型"""

    id: int = Field(..., description="菜单ID")
    name: str = Field(..., description="菜单名称")
    path: Optional[str] = Field(None, description="菜单路径")
    component: Optional[str] = Field(None, description="组件名称")
    icon: Optional[str] = Field(None, description="图标")
    children: List["MenuTree"] = Field(default_factory=list, description="子菜单")
    sort_order: int = Field(default=0, description="排序")
    is_visible: bool = Field(default=True, description="是否可见")


class UserMenuResponse(BaseModel):
    """用户菜单响应模型"""

    id: int = Field(..., description="菜单ID")
    name: str = Field(..., description="菜单名称")
    path: Optional[str] = Field(None, description="菜单路径")
    component: Optional[str] = Field(None, description="组件名称")
    icon: Optional[str] = Field(None, description="图标")
    children: List["UserMenuResponse"] = Field(default_factory=list, description="子菜单")
    sort_order: int = Field(default=0, description="排序")
