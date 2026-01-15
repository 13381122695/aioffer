"""
点数交易模型
创建日期: 2025-01-08
用途: 点数充值和消费记录
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from config.database import Base


class PointTransaction(Base):
    """点数交易记录表"""

    __tablename__ = "point_transactions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    type = Column(Integer, nullable=False, comment="交易类型: 1充值, 2消费, 3退款")
    points = Column(Integer, nullable=False, comment="交易点数")
    balance_after = Column(Integer, nullable=False, comment="交易后余额")
    amount = Column(Numeric(10, 2), nullable=True, comment="金额（充值时）")
    description = Column(Text, nullable=True, comment="交易描述")
    related_id = Column(Integer, nullable=True, comment="关联ID（订单ID等）")
    related_type = Column(String(50), nullable=True, comment="关联类型")
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # 关联关系
    user = relationship("User", back_populates="point_transactions")

    def __repr__(self):
        return f"<PointTransaction(id={self.id}, user_id={self.user_id}, type={self.type}, points={self.points})>"

    @property
    def type_text(self) -> str:
        """交易类型文本"""
        type_map = {1: "充值", 2: "消费", 3: "退款"}
        return type_map.get(self.type, "未知类型")

    @property
    def is_recharge(self) -> bool:
        """是否充值"""
        return self.type == 1

    @property
    def is_consumption(self) -> bool:
        """是否消费"""
        return self.type == 2

    @property
    def is_refund(self) -> bool:
        """是否退款"""
        return self.type == 3
