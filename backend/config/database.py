"""
数据库配置
创建日期: 2025-01-08
用途: 数据库连接和会话管理
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from config.settings import settings


class Base(DeclarativeBase):
    """数据库模型基类"""

    pass


# 数据库连接配置
SYNC_URL = settings.database_url
ASYNC_URL = SYNC_URL

# 自动转换异步驱动
if "sqlite" in SYNC_URL:
    if "aiosqlite" not in SYNC_URL:
        ASYNC_URL = SYNC_URL.replace("sqlite://", "sqlite+aiosqlite://")
elif "mysql" in SYNC_URL:
    if "pymysql" in SYNC_URL:
        ASYNC_URL = SYNC_URL.replace("pymysql", "aiomysql")
    elif "aiomysql" not in SYNC_URL:
        ASYNC_URL = SYNC_URL.replace("mysql://", "mysql+aiomysql://")

# 异步数据库引擎
async_engine = create_async_engine(
    ASYNC_URL,
    echo=settings.debug,
    pool_pre_ping=True,
)

# 异步会话工厂
AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# 同步数据库引擎（用于Alembic迁移）
sync_engine = create_engine(
    SYNC_URL,
    echo=settings.debug,
    pool_pre_ping=True,
)

# 同步会话工厂
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=sync_engine,
)


async def get_async_session():
    """获取异步数据库会话"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def get_sync_session():
    """获取同步数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def init_db():
    """初始化数据库表"""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
