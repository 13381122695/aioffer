"""
订单相关Pydantic模型
创建日期: 2025-01-08
用途: 订单管理的数据验证
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class OrderStatus(str, Enum):
    """订单状态枚举"""

    PENDING = "pending"
    PAID = "paid"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class OrderType(str, Enum):
    """订单类型枚举"""

    RECHARGE = "recharge"
    PURCHASE = "purchase"
    SUBSCRIPTION = "subscription"


class OrderBase(BaseModel):
    """订单基础模型"""

    user_id: int = Field(..., description="用户ID")
    order_type: OrderType = Field(..., description="订单类型")
    amount: float = Field(..., description="订单金额")
    points: int = Field(..., description="点数")
    description: Optional[str] = Field(None, max_length=500, description="订单描述")
    status: OrderStatus = Field(default=OrderStatus.PENDING, description="订单状态")
    payment_method: Optional[str] = Field(None, max_length=50, description="支付方式")
    transaction_id: Optional[str] = Field(None, max_length=100, description="交易ID")


class OrderCreate(OrderBase):
    """创建订单模型"""

    pass


class OrderUpdate(BaseModel):
    """更新订单模型"""

    amount: Optional[float] = Field(None, description="订单金额")
    points: Optional[int] = Field(None, description="点数")
    description: Optional[str] = Field(None, max_length=500, description="订单描述")
    status: Optional[OrderStatus] = Field(None, description="订单状态")
    payment_method: Optional[str] = Field(None, max_length=50, description="支付方式")
    transaction_id: Optional[str] = Field(None, max_length=100, description="交易ID")


class OrderResponse(OrderBase):
    """订单响应模型"""

    id: int = Field(..., description="订单ID")
    order_no: str = Field(..., description="订单号")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    paid_at: Optional[datetime] = Field(None, description="支付时间")

    class Config:
        from_attributes = True


class OrderList(BaseModel):
    """订单列表响应模型"""

    items: List[OrderResponse] = Field(..., description="订单列表")
    total: int = Field(..., description="总数")
    page: int = Field(..., description="当前页码")
    size: int = Field(..., description="每页数量")


class OrderStats(BaseModel):
    """订单统计模型"""

    total_orders: int = Field(..., description="总订单数")
    total_amount: float = Field(..., description="总金额")
    pending_orders: int = Field(..., description="待处理订单数")
    paid_orders: int = Field(..., description="已支付订单数")
    cancelled_orders: int = Field(..., description="已取消订单数")
    refunded_orders: int = Field(..., description="已退款订单数")
    monthly_revenue: float = Field(..., description="月收入")


class PaymentRequest(BaseModel):
    """支付请求模型"""

    order_id: int = Field(..., description="订单ID")
    payment_method: str = Field(..., description="支付方式")
    amount: float = Field(..., description="支付金额")


class PaymentResponse(BaseModel):
    """支付响应模型"""

    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="消息")
    transaction_id: Optional[str] = Field(None, description="交易ID")
    payment_url: Optional[str] = Field(None, description="支付链接")
