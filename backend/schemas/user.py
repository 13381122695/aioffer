"""
用户数据验证模式
创建日期: 2025-01-08
用途: 用户相关的数据验证和序列化
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UserBase(BaseModel):
    """用户基础模式"""

    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: Optional[EmailStr] = Field(None, description="邮箱")
    full_name: Optional[str] = Field(None, max_length=100, description="全名")
    avatar_url: Optional[str] = Field(None, max_length=255, description="头像URL")
    phone: Optional[str] = Field(None, max_length=20, description="手机号")
    status: int = Field(1, ge=1, le=3, description="状态: 1正常, 2禁用, 3删除")
    user_type: int = Field(1, ge=1, le=3, description="用户类型: 1普通用户, 2会员, 3管理员")


class UserCreate(UserBase):
    """用户创建模式"""

    password: Optional[str] = Field(
        None, min_length=6, max_length=100, description="密码"
    )
    role: Optional[int] = Field(None, description="角色ID (兼容前端)")
    is_active: Optional[bool] = Field(None, description="是否活跃 (兼容前端)")


class UserUpdate(BaseModel):
    """用户更新模式"""

    nickname: Optional[str] = Field(None, max_length=50, description="昵称")
    avatar: Optional[str] = Field(None, max_length=255, description="头像URL")
    email: Optional[EmailStr] = Field(None, description="邮箱")
    phone: Optional[str] = Field(None, max_length=20, description="手机号")
    status: Optional[int] = Field(None, ge=1, le=3, description="状态")
    user_type: Optional[int] = Field(None, ge=1, le=3, description="用户类型")
    role: Optional[int] = Field(None, description="角色ID (兼容前端)")
    is_active: Optional[bool] = Field(None, description="是否活跃 (兼容前端)")


class UserResponse(UserBase):
    """用户响应模式"""

    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserListResponse(BaseModel):
    """用户列表响应模式"""

    items: List[UserResponse]
    total: int
    page: int
    size: int
    pages: int


class UserAuthResponse(BaseModel):
    """用户认证响应模式"""

    id: int
    auth_type: str = Field(..., description="认证类型: email, wechat, wechat_qr, phone")
    auth_key: Optional[str] = Field(None, description="认证标识")
    is_verified: bool = Field(False, description="是否已验证")
    verified_at: Optional[datetime] = Field(None, description="验证时间")
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RechargeRequest(BaseModel):
    """充值请求模式"""

    user_id: int = Field(..., description="用户ID")
    points: int = Field(..., ge=1, description="充值点数")
    amount: float = Field(..., ge=0.01, description="充值金额")
    payment_method: str = Field(..., description="支付方式")
    description: Optional[str] = Field(None, description="备注")
