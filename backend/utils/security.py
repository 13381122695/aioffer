"""
安全工具
创建日期: 2025-01-08
用途: JWT令牌生成和验证、密码加密等安全功能
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from config.database import get_async_session
from models.user import User
from config import settings


# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """获取密码哈希"""
    return pwd_context.hash(password)


def create_access_token(
    data: Dict[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    """创建访问令牌"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.access_token_expire_minutes
        )

    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(
        to_encode, settings.secret_key, algorithm=settings.algorithm
    )
    return encoded_jwt


def create_refresh_token(data: Dict[str, Any]) -> str:
    """创建刷新令牌"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(
        to_encode, settings.secret_key, algorithm=settings.algorithm
    )
    return encoded_jwt


def decode_token(token: str) -> Dict[str, Any]:
    """解码令牌"""
    try:
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.algorithm]
        )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )


def verify_access_token(token: str) -> Dict[str, Any]:
    """验证访问令牌"""
    payload = decode_token(token)
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的访问令牌类型",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload


def verify_refresh_token(token: str) -> Dict[str, Any]:
    """验证刷新令牌"""
    payload = decode_token(token)
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的刷新令牌类型",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload


def generate_order_no() -> str:
    """生成订单号"""
    from datetime import datetime
    import random

    now = datetime.now()
    date_str = now.strftime("%Y%m%d%H%M%S")
    random_str = str(random.randint(100000, 999999))
    return f"ORD{date_str}{random_str}"


def generate_random_string(length: int = 8) -> str:
    """生成随机字符串"""
    import string
    import secrets

    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def mask_sensitive_data(data: str, start: int = 3, end: int = 3) -> str:
    """脱敏处理"""
    if len(data) <= start + end:
        return "*" * len(data)

    masked_part = "*" * (len(data) - start - end)
    return data[:start] + masked_part + data[-end:]


# HTTP认证方案
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_async_session),
) -> User:
    """获取当前用户"""
    token = credentials.credentials
    payload = verify_access_token(token)

    user_id = int(payload.get("sub"))
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的用户ID")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")

    return user


class SecurityManager:
    """安全管理器"""

    @staticmethod
    def hash_password(password: str) -> str:
        """哈希密码"""
        return get_password_hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """验证密码"""
        return verify_password(plain_password, hashed_password)

    @staticmethod
    def verify_access_token(token: str) -> Dict[str, Any]:
        """验证访问令牌"""
        return verify_access_token(token)

    @staticmethod
    def verify_refresh_token(token: str) -> Dict[str, Any]:
        """验证刷新令牌"""
        return verify_refresh_token(token)

    @staticmethod
    def create_tokens(user_id: int, username: str, **kwargs) -> Dict[str, str]:
        """创建令牌对"""
        token_data = {"sub": str(user_id), "username": username, **kwargs}

        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.access_token_expire_minutes * 60,
        }

    @staticmethod
    def refresh_access_token(refresh_token: str) -> str:
        """刷新访问令牌"""
        payload = verify_refresh_token(refresh_token)
        user_id = int(payload.get("sub"))
        username = payload.get("username")

        if not user_id or not username:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的令牌数据"
            )

        return create_access_token({"sub": str(user_id), "username": username})
