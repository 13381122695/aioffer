"""
用户模型
创建日期: 2025-01-08
用途: 用户和用户认证数据模型
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Boolean,
    Text,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from config.database import Base


class User(Base):
    """用户表"""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(
        String(50), unique=True, nullable=False, index=True, comment="用户名"
    )
    email = Column(String(100), unique=True, nullable=True, index=True, comment="邮箱")
    password_hash = Column(String(255), nullable=True, comment="密码哈希")
    full_name = Column(String(100), nullable=True, comment="全名")
    avatar_url = Column(String(255), nullable=True, comment="头像URL")
    phone = Column(String(20), nullable=True, comment="手机号")
    status = Column(
        Integer, default=1, nullable=False, index=True, comment="状态: 1正常, 2禁用, 3删除"
    )
    user_type = Column(
        Integer, default=1, nullable=False, comment="用户类型: 1普通用户, 2会员, 3管理员"
    )
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
    auths = relationship(
        "UserAuth", back_populates="user", cascade="all, delete-orphan"
    )
    member = relationship(
        "Member", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    orders = relationship("Order", back_populates="user")
    point_transactions = relationship("PointTransaction", back_populates="user")
    roles = relationship("Role", secondary="user_roles", back_populates="users")
    login_logs = relationship("LoginLog", back_populates="user")

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"

    @property
    def is_active(self) -> bool:
        """是否活跃用户"""
        return self.status == 1

    @property
    def is_admin(self) -> bool:
        """是否管理员"""
        return self.user_type == 3

    @property
    def is_member(self) -> bool:
        """是否会员"""
        return self.user_type == 2


class UserAuth(Base):
    """用户认证表 - 支持多种登录方式"""

    __tablename__ = "user_auths"
    __table_args__ = (UniqueConstraint("auth_type", "auth_key", name="unique_auth"),)

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    auth_type = Column(
        String(20), nullable=False, comment="认证类型: email, wechat, wechat_qr, phone"
    )
    auth_key = Column(String(100), nullable=True, comment="认证标识: 邮箱、手机号、微信openid等")
    auth_secret = Column(String(255), nullable=True, comment="认证密钥: 密码、微信unionid等")
    wechat_nickname = Column(String(100), nullable=True, comment="微信昵称")
    wechat_avatar = Column(String(255), nullable=True, comment="微信头像")
    is_verified = Column(Boolean, default=False, nullable=False, comment="是否已验证")
    verified_at = Column(DateTime(timezone=True), nullable=True, comment="验证时间")
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
    user = relationship("User", back_populates="auths")

    def __repr__(self):
        return f"<UserAuth(id={self.id}, user_id={self.user_id}, auth_type='{self.auth_type}')>"

    @property
    def is_wechat_auth(self) -> bool:
        """是否微信认证"""
        return self.auth_type in ["wechat", "wechat_qr"]

    @property
    def is_email_auth(self) -> bool:
        """是否邮箱认证"""
        return self.auth_type == "email"

    @property
    def is_phone_auth(self) -> bool:
        """是否手机认证"""
        return self.auth_type == "phone"


class EmailVerificationCode(Base):
    """邮箱验证码表"""

    __tablename__ = "email_verification_codes"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String(100), nullable=False, index=True, comment="邮箱")
    purpose = Column(String(30), nullable=False, index=True, comment="用途: register")
    code_hash = Column(String(255), nullable=False, comment="验证码哈希")
    expires_at = Column(DateTime(timezone=True), nullable=False, comment="过期时间")
    used_at = Column(DateTime(timezone=True), nullable=True, comment="使用时间")
    ip = Column(String(45), nullable=True, comment="请求IP")
    user_agent = Column(Text, nullable=True, comment="User-Agent")
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self):
        return f"<EmailVerificationCode(id={self.id}, email='{self.email}', purpose='{self.purpose}')>"

    @property
    def is_used(self) -> bool:
        """是否已使用"""
        return self.used_at is not None


class LoginLog(Base):
    """登录日志表"""

    __tablename__ = "login_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    auth_type = Column(
        String(20), nullable=False, index=True, comment="登录类型: email, username"
    )
    identifier = Column(String(100), nullable=True, index=True, comment="登录标识: 邮箱或用户名")
    ip = Column(String(45), nullable=True, index=True, comment="登录IP")
    user_agent = Column(Text, nullable=True, comment="User-Agent")
    success = Column(Boolean, default=False, nullable=False, index=True, comment="是否成功")
    failure_reason = Column(String(255), nullable=True, comment="失败原因")
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user = relationship("User", back_populates="login_logs")

    def __repr__(self):
        return (
            f"<LoginLog(id={self.id}, user_id={self.user_id}, success={self.success})>"
        )
