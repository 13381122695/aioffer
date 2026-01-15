"""
配置文件
创建日期: 2025-01-08
用途: 系统配置管理
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # 数据库配置
    database_url: str = "mysql+pymysql://root:password@localhost:3306/admin_system"
    mysql_host: str = "localhost"
    mysql_port: int = 3306
    mysql_user: str = "root"
    mysql_password: str = "password"
    mysql_database: str = "admin_system"

    # Redis配置
    redis_url: str = "redis://localhost:6379/0"
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None

    # JWT配置
    secret_key: str = "your-secret-key-here"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # 微信配置
    wechat_app_id: Optional[str] = None
    wechat_app_secret: Optional[str] = None
    wechat_token: Optional[str] = None
    wechat_encoding_aes_key: Optional[str] = None

    # 邮件配置
    smtp_host: Optional[str] = None
    smtp_port: int = 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_use_tls: bool = True
    smtp_use_ssl: bool = False
    email_from: Optional[str] = None
    email_from_name: Optional[str] = None
    email_product_name: str = "会员管理"
    email_code_length: int = 6
    email_code_expire_minutes: int = 10
    email_code_resend_interval_seconds: int = 60
    email_code_daily_limit_per_email: int = 10
    email_code_daily_limit_per_ip: int = 50

    # 文件上传配置
    upload_dir: str = "./uploads"
    max_file_size: int = 10485760  # 10MB

    # 日志配置
    log_level: str = "INFO"
    log_file: str = "./logs/app.log"

    # 系统配置
    debug: bool = True
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = True

    # 安全配置
    bcrypt_rounds: int = 12
    rate_limit: str = "100/minute"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
