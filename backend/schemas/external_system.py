"""
外部系统相关Pydantic模型
创建日期: 2025-01-08
用途: 外部系统集成配置的数据验证
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime


class ExternalSystemBase(BaseModel):
    """外部系统基础模型"""

    name: str = Field(..., min_length=1, max_length=50, description="系统名称")
    system_type: str = Field(
        ..., pattern="^(api|page|iframe)$", description="系统类型: api, page, iframe"
    )
    page_url: Optional[str] = Field(None, max_length=255, description="页面URL")
    api_key: Optional[str] = Field(None, max_length=255, description="API密钥")
    api_secret: Optional[str] = Field(None, max_length=255, description="API密钥")
    endpoint_url: Optional[str] = Field(None, max_length=255, description="API端点")
    config: Optional[Dict[str, Any]] = Field(default_factory=dict, description="配置信息")
    is_active: bool = Field(default=True, description="是否启用")


class ExternalSystemCreate(ExternalSystemBase):
    """创建外部系统模型"""

    pass


class ExternalSystemUpdate(BaseModel):
    """更新外部系统模型"""

    name: Optional[str] = Field(None, min_length=1, max_length=50, description="系统名称")
    system_type: Optional[str] = Field(
        None, pattern="^(api|page|iframe)$", description="系统类型"
    )
    page_url: Optional[str] = Field(None, max_length=255, description="页面URL")
    api_key: Optional[str] = Field(None, max_length=255, description="API密钥")
    api_secret: Optional[str] = Field(None, max_length=255, description="API密钥")
    endpoint_url: Optional[str] = Field(None, max_length=255, description="API端点")
    config: Optional[Dict[str, Any]] = Field(None, description="配置信息")
    is_active: Optional[bool] = Field(None, description="是否启用")


class ExternalSystemResponse(ExternalSystemBase):
    """外部系统响应模型"""

    id: int = Field(..., description="系统ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


class ExternalSystemList(BaseModel):
    """外部系统列表响应模型"""

    items: List[ExternalSystemResponse] = Field(..., description="系统列表")
    total: int = Field(..., description="总数")
    page: int = Field(..., description="当前页码")
    size: int = Field(..., description="每页数量")


class ExternalSystemAccess(BaseModel):
    """外部系统访问模型"""

    system_id: int = Field(..., description="系统ID")
    user_id: int = Field(..., description="用户ID")
    access_token: Optional[str] = Field(None, description="访问令牌")
    expires_at: Optional[datetime] = Field(None, description="过期时间")


class ExternalSystemIntegration(BaseModel):
    """外部系统集成配置模型"""

    system_id: int = Field(..., description="系统ID")
    integration_type: str = Field(..., pattern="^(iframe|sso|api)$", description="集成类型")
    config: Dict[str, Any] = Field(default_factory=dict, description="集成配置")


class PageIntegrationConfig(BaseModel):
    """页面系统集成配置"""

    url: str = Field(..., description="页面URL")
    width: Optional[str] = Field(default="100%", description="宽度")
    height: Optional[str] = Field(default="600px", description="高度")
    allow_fullscreen: bool = Field(default=True, description="允许全屏")
    sandbox: Optional[List[str]] = Field(default_factory=list, description="沙箱配置")


class SSOIntegrationConfig(BaseModel):
    """SSO集成配置"""

    sso_url: str = Field(..., description="SSO登录URL")
    callback_url: str = Field(..., description="回调URL")
    client_id: str = Field(..., description="客户端ID")
    client_secret: str = Field(..., description="客户端密钥")
    scope: Optional[str] = Field(default="openid profile", description="权限范围")
