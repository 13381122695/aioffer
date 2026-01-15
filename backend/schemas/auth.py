"""
认证数据验证模式
创建日期: 2025-01-08
用途: 登录、注册等认证相关的数据验证和序列化
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class LoginRequest(BaseModel):
    """登录请求模式"""

    auth_type: str = Field(..., description="认证类型: email, username")
    email: Optional[EmailStr] = Field(None, description="邮箱（邮箱登录时使用）")
    password: Optional[str] = Field(None, description="密码（邮箱/用户名登录时使用）")
    username: Optional[str] = Field(None, description="用户名（用户名登录时使用）")


class TokenResponse(BaseModel):
    """Token响应模式"""

    access_token: str = Field(..., description="访问令牌")
    refresh_token: str = Field(..., description="刷新令牌")
    token_type: str = Field("bearer", description="令牌类型")
    expires_in: int = Field(..., description="过期时间（秒）")
    user: dict = Field(..., description="用户信息")


class RefreshTokenRequest(BaseModel):
    """刷新Token请求模式"""

    refresh_token: str = Field(..., description="刷新令牌")


class WeChatLoginRequest(BaseModel):
    """微信登录请求模式"""

    code: str = Field(..., description="微信授权码")
    state: Optional[str] = Field(None, description="状态参数")


class WeChatQRLoginRequest(BaseModel):
    """微信扫码登录请求模式"""

    scene_id: str = Field(..., description="场景ID")


class PhoneLoginRequest(BaseModel):
    """手机登录请求模式"""

    phone: str = Field(..., description="手机号")
    sms_code: str = Field(..., description="短信验证码")


class EmailLoginRequest(BaseModel):
    """邮箱登录请求模式"""

    email: EmailStr = Field(..., description="邮箱")
    password: str = Field(..., description="密码")


class UsernameLoginRequest(BaseModel):
    """用户名登录请求模式"""

    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")


class RegisterRequest(BaseModel):
    """注册请求模式"""

    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: Optional[EmailStr] = Field(None, description="邮箱")
    password: Optional[str] = Field(None, min_length=6, description="密码")
    email_code: Optional[str] = Field(
        None, min_length=4, max_length=20, description="邮箱验证码"
    )
    full_name: Optional[str] = Field(None, max_length=100, description="全名")
    auth_type: str = Field("email", description="注册方式: email")


class SendEmailCodeRequest(BaseModel):
    """发送邮箱验证码请求模式"""

    email: EmailStr = Field(..., description="邮箱")
    purpose: str = Field(
        "register", description="用途: register, reset_password, change_email"
    )


class ChangePasswordRequest(BaseModel):
    """修改密码请求模式"""

    old_password: str = Field(..., description="旧密码")
    new_password: str = Field(..., min_length=6, description="新密码")


class UserAuthResponse(BaseModel):
    """用户认证响应模式"""

    id: int
    auth_type: str = Field(..., description="认证类型")
    auth_key: Optional[str] = Field(None, description="认证标识")
    is_verified: bool = Field(False, description="是否已验证")
    verified_at: Optional[datetime] = Field(None, description="验证时间")
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
