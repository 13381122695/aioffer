"""
会员模型
创建日期: 2025-01-08
用途: 会员信息和点数管理
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, Numeric, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from config.database import Base


class Member(Base):
    """会员信息表"""

    __tablename__ = "members"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    member_level = Column(Integer, default=1, nullable=False, comment="会员等级")
    points = Column(Integer, default=0, nullable=False, comment="积分点数")
    balance = Column(Numeric(10, 2), default=0.00, nullable=False, comment="余额")
    expired_at = Column(DateTime(timezone=True), nullable=True, comment="会员到期时间")
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
    user = relationship("User", back_populates="member")

    def __repr__(self):
        return f"<Member(id={self.id}, user_id={self.user_id}, level={self.member_level}, points={self.points})>"

    @property
    def is_expired(self) -> bool:
        """会员是否已过期"""
        if not self.expired_at:
            return False
        expired_at = self.expired_at
        if expired_at.tzinfo is None:
            expired_at = expired_at.replace(tzinfo=timezone.utc)
        return datetime.now(timezone.utc) > expired_at

    @property
    def is_valid_member(self) -> bool:
        """是否为有效会员"""
        return self.member_level > 1 and not self.is_expired

    def add_points(self, points: int, description: str = ""):
        """增加积分"""
        self.points += points
        return self.points

    def deduct_points(self, points: int, description: str = ""):
        """扣除积分"""
        if self.points >= points:
            self.points -= points
            return True, self.points
        return False, self.points

    def add_balance(self, amount: float, description: str = ""):
        """增加余额"""
        self.balance += amount
        return float(self.balance)

    def deduct_balance(self, amount: float, description: str = ""):
        """扣除余额"""
        if float(self.balance) >= amount:
            self.balance -= amount
            return True, float(self.balance)
        return False, float(self.balance)
