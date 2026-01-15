"""
角色权限相关Pydantic模型
创建日期: 2025-01-08
用途: 角色和权限管理的数据验证
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class PermissionBase(BaseModel):
    """权限基础模型"""

    name: str = Field(..., min_length=1, max_length=50, description="权限名称")
    code: str = Field(..., min_length=1, max_length=50, description="权限代码")
    description: Optional[str] = Field(None, max_length=200, description="权限描述")
    module: Optional[str] = Field(None, max_length=50, description="所属模块")
    is_active: bool = Field(default=True, description="是否激活")


class PermissionCreate(PermissionBase):
    """创建权限模型"""

    pass


class PermissionUpdate(BaseModel):
    """更新权限模型"""

    name: Optional[str] = Field(None, min_length=1, max_length=50, description="权限名称")
    code: Optional[str] = Field(None, min_length=1, max_length=50, description="权限代码")
    description: Optional[str] = Field(None, max_length=200, description="权限描述")
    module: Optional[str] = Field(None, max_length=50, description="所属模块")
    is_active: Optional[bool] = Field(None, description="是否激活")


class PermissionResponse(PermissionBase):
    """权限响应模型"""

    id: int = Field(..., description="权限ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


class RoleBase(BaseModel):
    """角色基础模型"""

    name: str = Field(..., min_length=1, max_length=50, description="角色名称")
    description: Optional[str] = Field(None, max_length=200, description="角色描述")
    is_active: bool = Field(default=True, description="是否激活")


class RoleCreate(RoleBase):
    """创建角色模型"""

    permission_ids: Optional[List[int]] = Field(
        default_factory=list, description="权限ID列表"
    )


class RoleUpdate(BaseModel):
    """更新角色模型"""

    name: Optional[str] = Field(None, min_length=1, max_length=50, description="角色名称")
    description: Optional[str] = Field(None, max_length=200, description="角色描述")
    is_active: Optional[bool] = Field(None, description="是否激活")
    permission_ids: Optional[List[int]] = Field(None, description="权限ID列表")


class RoleResponse(RoleBase):
    """角色响应模型"""

    id: int = Field(..., description="角色ID")
    permissions: List[PermissionResponse] = Field(
        default_factory=list, description="权限列表"
    )
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


class RoleList(BaseModel):
    """角色列表响应模型"""

    items: List[RoleResponse] = Field(..., description="角色列表")
    total: int = Field(..., description="总数")
    page: int = Field(..., description="当前页码")
    size: int = Field(..., description="每页数量")


class RolePermission(BaseModel):
    """角色权限关联模型"""

    role_id: int = Field(..., description="角色ID")
    permission_id: int = Field(..., description="权限ID")


class UserRole(BaseModel):
    """用户角色关联模型"""

    user_id: int = Field(..., description="用户ID")
    role_id: int = Field(..., description="角色ID")
