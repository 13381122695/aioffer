"""
缓存工具
创建日期: 2025-01-08
用途: Redis缓存操作工具类
"""

import json
import redis
from typing import Any, Optional, Union
from config.settings import settings

# Redis客户端实例
redis_client = redis.Redis(
    host=settings.redis_host,
    port=settings.redis_port,
    db=settings.redis_db,
    password=settings.redis_password,
    decode_responses=True,
)


class CacheManager:
    """缓存管理器"""

    @staticmethod
    def get(key: str) -> Optional[str]:
        """获取缓存值"""
        try:
            return redis_client.get(key)
        except Exception as e:
            print(f"Redis get error: {e}")
            return None

    @staticmethod
    def set(key: str, value: Union[str, dict, list], expire: int = 3600) -> bool:
        """设置缓存值"""
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            return redis_client.setex(key, expire, value)
        except Exception as e:
            print(f"Redis set error: {e}")
            return False

    @staticmethod
    def delete(key: str) -> bool:
        """删除缓存"""
        try:
            return bool(redis_client.delete(key))
        except Exception as e:
            print(f"Redis delete error: {e}")
            return False

    @staticmethod
    def exists(key: str) -> bool:
        """检查缓存是否存在"""
        try:
            return bool(redis_client.exists(key))
        except Exception as e:
            print(f"Redis exists error: {e}")
            return False

    @staticmethod
    def hget(name: str, key: str) -> Optional[str]:
        """获取哈希字段值"""
        try:
            return redis_client.hget(name, key)
        except Exception as e:
            print(f"Redis hget error: {e}")
            return None

    @staticmethod
    def hset(name: str, key: str, value: Union[str, dict, list]) -> bool:
        """设置哈希字段值"""
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            return bool(redis_client.hset(name, key, value))
        except Exception as e:
            print(f"Redis hset error: {e}")
            return False

    @staticmethod
    def hdel(name: str, key: str) -> bool:
        """删除哈希字段"""
        try:
            return bool(redis_client.hdel(name, key))
        except Exception as e:
            print(f"Redis hdel error: {e}")
            return False

    @staticmethod
    def hkeys(name: str) -> list:
        """获取哈希所有字段名"""
        try:
            return redis_client.hkeys(name)
        except Exception as e:
            print(f"Redis hkeys error: {e}")
            return []


# 创建缓存管理器实例
cache_manager = CacheManager()
