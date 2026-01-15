"""
日志工具
创建日期: 2025-01-08
用途: 日志配置和管理
"""

import logging
import logging.handlers
import os
from datetime import datetime
from config import settings


def setup_logging():
    """设置日志配置"""
    # 创建日志目录
    log_dir = os.path.dirname(settings.log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # 配置根日志器
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, settings.log_level.upper()))

    # 创建格式器
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # 文件处理器（按日期轮转）
    file_handler = logging.handlers.TimedRotatingFileHandler(
        settings.log_file, when="midnight", interval=1, backupCount=30, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 设置特定模块的日志级别
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)

    return logger


def get_logger(name: str = None):
    """获取日志器"""
    return logging.getLogger(name)
