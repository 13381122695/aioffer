"""
会员相关Pydantic模型
创建日期: 2025-01-08
用途: 会员管理的数据验证
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class MemberBase(BaseModel):
    """会员基础模型"""

    user_id: int = Field(..., description="用户ID")
    member_type: str = Field(..., description="会员类型")
    start_date: datetime = Field(..., description="开始日期")
    end_date: Optional[datetime] = Field(None, description="结束日期")
    is_active: bool = Field(default=True, description="是否激活")
    points: int = Field(default=0, description="会员点数")


class MemberCreate(MemberBase):
    """创建会员模型"""

    pass


class MemberUpdate(BaseModel):
    """更新会员模型"""

    member_type: Optional[str] = Field(None, description="会员类型")
    start_date: Optional[datetime] = Field(None, description="开始日期")
    end_date: Optional[datetime] = Field(None, description="结束日期")
    is_active: Optional[bool] = Field(None, description="是否激活")
    points: Optional[int] = Field(None, description="会员点数")


class MemberResponse(MemberBase):
    """会员响应模型"""

    id: int = Field(..., description="会员ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    model_config = {"from_attributes": True}


class MemberList(BaseModel):
    """会员列表响应模型"""

    items: List[MemberResponse] = Field(..., description="会员列表")
    total: int = Field(..., description="总数")
    page: int = Field(..., description="当前页码")
    size: int = Field(..., description="每页数量")


class MemberType(BaseModel):
    """会员类型模型"""

    id: int = Field(..., description="类型ID")
    name: str = Field(..., description="类型名称")
    description: Optional[str] = Field(None, description="类型描述")
    price: float = Field(..., description="价格")
    duration_days: int = Field(..., description="持续天数")
    points: int = Field(..., description="包含点数")
    is_active: bool = Field(default=True, description="是否激活")


class MemberStats(BaseModel):
    """会员统计模型"""

    total_members: int = Field(..., description="总会员数")
    active_members: int = Field(..., description="活跃会员数")
    expired_members: int = Field(..., description="过期会员数")
    total_points: int = Field(..., description="总点数")
    monthly_revenue: float = Field(..., description="月收入")
