"""
FastAPI主应用
创建日期: 2025-01-08
用途: 会员管理系统API服务入口
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware
import uvicorn
import logging
from contextlib import asynccontextmanager

from config import settings
from config.database import init_db
from routers import auth, users, roles, menus, orders, external_systems, recharge
from utils.logger import setup_logging


# 设置日志
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    logger.info("正在初始化数据库...")
    await init_db()
    logger.info("数据库初始化完成")

    yield

    # 关闭时执行
    logger.info("应用正在关闭...")


# 创建FastAPI应用
app = FastAPI(
    title="会员管理系统API",
    description="功能完整的会员管理系统，支持用户管理、权限控制、支付系统、外部系统集成",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该设置具体的域名
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")

# 注册路由
app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
app.include_router(users.router, prefix="/api/users", tags=["用户管理"])
app.include_router(roles.router, prefix="/api/roles", tags=["权限管理"])
app.include_router(menus.router, prefix="/api/menus", tags=["菜单管理"])
app.include_router(orders.router, prefix="/api/orders", tags=["订单管理"])
app.include_router(
    external_systems.router, prefix="/api/external-systems", tags=["外部系统"]
)
app.include_router(recharge.router, prefix="/api/recharge", tags=["充值"])

# 静态文件服务
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "欢迎使用会员管理系统API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "timestamp": "2025-01-08T00:00:00Z"}


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理"""
    logger.error(f"未处理的异常: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "code": 500,
            "message": "服务器内部错误",
            "detail": str(exc) if settings.debug else "请联系管理员",
        },
    )


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_level=settings.log_level.lower(),
    )
