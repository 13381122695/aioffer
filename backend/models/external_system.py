"""
外部系统模型
创建日期: 2025-01-08
用途: 外部页面系统集成配置
"""

from typing import Optional, Dict, Any
from sqlalchemy import Column, Integer, String, DateTime, Boolean, JSON, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from config.database import Base


class ExternalSystem(Base):
    """外部系统配置表"""

    __tablename__ = "external_systems"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(50), nullable=False, comment="系统名称")
    system_type = Column(String(20), nullable=False, comment="系统类型: api, page, iframe")
    page_url = Column(String(255), nullable=True, comment="页面URL")
    api_key = Column(String(255), nullable=True, comment="API密钥")
    api_secret = Column(String(255), nullable=True, comment="API密钥")
    endpoint_url = Column(String(255), nullable=True, comment="API端点")
    config = Column(JSON, nullable=True, comment="配置信息")
    is_active = Column(Boolean, default=True, nullable=False, comment="是否启用")
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self):
        return f"<ExternalSystem(id={self.id}, name='{self.name}', type='{self.system_type}')>"

    @property
    def integration_config(self) -> Dict[str, Any]:
        """获取集成配置"""
        if not self.config:
            return {}
        return self.config

    @property
    def is_page_system(self) -> bool:
        """是否为页面系统"""
        return self.system_type in ["page", "iframe"]

    @property
    def is_api_system(self) -> bool:
        """是否为API系统"""
        return self.system_type == "api"

    def get_config_value(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        if not self.config:
            return default
        return self.config.get(key, default)

    def set_config_value(self, key: str, value: Any):
        """设置配置值"""
        if not self.config:
            self.config = {}
        self.config[key] = value

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "system_type": self.system_type,
            "page_url": self.page_url,
            "endpoint_url": self.endpoint_url,
            "config": self.config,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
