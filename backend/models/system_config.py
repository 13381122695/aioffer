"""
系统配置模型
创建日期: 2025-01-08
用途: 系统参数配置
"""

from typing import Optional, Dict, Any
from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func
from config.database import Base


class SystemConfig(Base):
    """系统配置表"""

    __tablename__ = "system_configs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    config_key = Column(
        String(100), unique=True, nullable=False, index=True, comment="配置键"
    )
    config_value = Column(Text, nullable=True, comment="配置值")
    description = Column(Text, nullable=True, comment="配置描述")
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
        return f"<SystemConfig(id={self.id}, key='{self.config_key}', value='{self.config_value}')>"

    @property
    def value(self) -> Optional[str]:
        """获取配置值"""
        return self.config_value

    @value.setter
    def value(self, value: Optional[str]):
        """设置配置值"""
        self.config_value = value

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "config_key": self.config_key,
            "config_value": self.config_value,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
