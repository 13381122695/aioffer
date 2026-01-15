"""
订单模型
创建日期: 2025-01-08
用途: 订单和支付管理
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from config.database import Base


class Order(Base):
    """订单表"""

    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    order_no = Column(
        String(32), unique=True, nullable=False, index=True, comment="订单号"
    )
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_id = Column(Integer, nullable=True, comment="产品ID")
    product_type = Column(
        String(20), nullable=False, comment="产品类型: points, member, service"
    )
    amount = Column(Numeric(10, 2), nullable=False, comment="订单金额")
    quantity = Column(Integer, default=1, nullable=False, comment="数量")
    status = Column(
        Integer,
        default=1,
        nullable=False,
        index=True,
        comment="状态: 1待支付, 2已支付, 3已取消, 4已退款",
    )
    payment_method = Column(String(20), nullable=True, comment="支付方式")
    payment_time = Column(DateTime(timezone=True), nullable=True, comment="支付时间")
    description = Column(Text, nullable=True, comment="订单描述")
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # 关联关系
    user = relationship("User", back_populates="orders")

    def __repr__(self):
        return f"<Order(id={self.id}, order_no='{self.order_no}', user_id={self.user_id}, amount={self.amount})>"

    @property
    def is_paid(self) -> bool:
        """是否已支付"""
        return self.status == 2

    @property
    def is_cancelled(self) -> bool:
        """是否已取消"""
        return self.status == 3

    @property
    def is_refunded(self) -> bool:
        """是否已退款"""
        return self.status == 4

    @property
    def status_text(self) -> str:
        """状态文本"""
        status_map = {1: "待支付", 2: "已支付", 3: "已取消", 4: "已退款"}
        return status_map.get(self.status, "未知状态")

    def can_pay(self) -> bool:
        """是否可以支付"""
        return self.status == 1

    def can_cancel(self) -> bool:
        """是否可以取消"""
        return self.status == 1

    def can_refund(self) -> bool:
        """是否可以退款"""
        return self.status == 2
