"""
外部系统集成路由器
创建日期: 2025-01-08
用途: 外部页面系统集成管理，支持iframe和SSO集成
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import time
from jose import JWTError, jwt
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from config.database import get_sync_session
from config.settings import settings
from models.user import User
from models.external_system import ExternalSystem
from schemas.external_system import (
    ExternalSystemCreate,
    ExternalSystemUpdate,
    ExternalSystemResponse,
    ExternalSystemList,
    ExternalSystemAccess,
    ExternalSystemIntegration,
    PageIntegrationConfig,
    SSOIntegrationConfig,
)
from utils.security import get_current_user
from utils.logger import get_logger

logger = get_logger(__name__)


router = APIRouter()


def generate_access_token(system_id: int, user_id: int, expires_at: datetime) -> str:
    payload = {
        "type": "external_system_access",
        "system_id": system_id,
        "user_id": user_id,
        "exp": int(expires_at.timestamp()),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def get_user_role_name(user: User) -> str:
    if user.is_admin:
        return "admin"
    if user.is_member:
        return "member"
    return "user"


def sanitize_integration_config(
    config: Dict[str, Any], include_secrets: bool
) -> Dict[str, Any]:
    if include_secrets:
        return config

    blocked_keys = {
        "api_secret",
        "api_key",
        "client_secret",
        "secret",
        "token",
        "access_token",
        "refresh_token",
    }
    return {k: v for k, v in config.items() if k not in blocked_keys}


def user_can_access_external_system(system: ExternalSystem, user: User) -> bool:
    if user.is_admin:
        return True

    allowed_user_ids = system.get_config_value("allowed_user_ids")
    if isinstance(allowed_user_ids, list):
        try:
            allowed_user_ids_int = {int(v) for v in allowed_user_ids}
        except (TypeError, ValueError):
            allowed_user_ids_int = set()
        if allowed_user_ids_int and user.id not in allowed_user_ids_int:
            return False

    allowed_roles = system.get_config_value("allowed_roles")
    if isinstance(allowed_roles, list):
        allowed_roles_str = {str(v) for v in allowed_roles}
        if allowed_roles_str and get_user_role_name(user) not in allowed_roles_str:
            return False

    return True


@router.get("/", response_model=ExternalSystemList)
def get_external_systems(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=1, le=100, description="每页数量"),
    system_type: Optional[str] = Query(None, description="系统类型"),
    is_active: Optional[bool] = Query(None, description="是否启用"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    db: Session = Depends(get_sync_session),
    current_user: User = Depends(get_current_user),
):
    """
    获取外部系统列表
    需要管理员权限
    """
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="需要管理员权限")

    # 构建查询条件
    query = db.query(ExternalSystem)

    if system_type:
        query = query.filter(ExternalSystem.system_type == system_type)

    if is_active is not None:
        query = query.filter(ExternalSystem.is_active == is_active)

    if search:
        query = query.filter(
            or_(
                ExternalSystem.name.contains(search),
                ExternalSystem.endpoint_url.contains(search),
            )
        )

    # 计算总数
    total = query.count()

    # 分页查询
    systems = query.offset((page - 1) * size).limit(size).all()

    logger.info(f"用户 {current_user.username} 查询外部系统列表，返回 {len(systems)} 条记录")

    return ExternalSystemList(
        items=[ExternalSystemResponse.from_orm(system) for system in systems],
        total=total,
        page=page,
        size=size,
    )


@router.post("/", response_model=ExternalSystemResponse)
def create_external_system(
    system_data: ExternalSystemCreate,
    db: Session = Depends(get_sync_session),
    current_user: User = Depends(get_current_user),
):
    """
    创建外部系统
    需要管理员权限
    """
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="需要管理员权限")

    # 检查名称是否已存在
    existing = (
        db.query(ExternalSystem).filter(ExternalSystem.name == system_data.name).first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="系统名称已存在")

    # 验证页面系统必须提供URL
    if system_data.system_type in ["page", "iframe"] and not system_data.page_url:
        raise HTTPException(status_code=400, detail="页面系统必须提供页面URL")

    # 创建系统
    system = ExternalSystem(**system_data.dict())
    db.add(system)
    db.commit()
    db.refresh(system)

    logger.info(f"用户 {current_user.username} 创建外部系统: {system.name}")

    return ExternalSystemResponse.from_orm(system)


@router.get("/{system_id}", response_model=ExternalSystemResponse)
def get_external_system(
    system_id: int,
    db: Session = Depends(get_sync_session),
    current_user: User = Depends(get_current_user),
):
    """
    获取外部系统详情
    需要管理员权限
    """
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="需要管理员权限")

    system = db.query(ExternalSystem).filter(ExternalSystem.id == system_id).first()
    if not system:
        raise HTTPException(status_code=404, detail="外部系统不存在")

    return ExternalSystemResponse.from_orm(system)


@router.put("/{system_id}", response_model=ExternalSystemResponse)
def update_external_system(
    system_id: int,
    system_data: ExternalSystemUpdate,
    db: Session = Depends(get_sync_session),
    current_user: User = Depends(get_current_user),
):
    """
    更新外部系统
    需要管理员权限
    """
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="需要管理员权限")

    system = db.query(ExternalSystem).filter(ExternalSystem.id == system_id).first()
    if not system:
        raise HTTPException(status_code=404, detail="外部系统不存在")

    # 检查名称是否与其他系统冲突
    if system_data.name:
        existing = (
            db.query(ExternalSystem)
            .filter(
                and_(
                    ExternalSystem.name == system_data.name,
                    ExternalSystem.id != system_id,
                )
            )
            .first()
        )
        if existing:
            raise HTTPException(status_code=400, detail="系统名称已存在")

    # 验证页面系统必须提供URL
    if system_data.system_type in ["page", "iframe"] and not system_data.page_url:
        raise HTTPException(status_code=400, detail="页面系统必须提供页面URL")

    # 更新字段
    update_data = system_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(system, field, value)

    db.commit()
    db.refresh(system)

    logger.info(f"用户 {current_user.username} 更新外部系统: {system.name}")

    return ExternalSystemResponse.model_validate(system)


@router.delete("/{system_id}")
def delete_external_system(
    system_id: int,
    db: Session = Depends(get_sync_session),
    current_user: User = Depends(get_current_user),
):
    """
    删除外部系统
    需要管理员权限
    """
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="需要管理员权限")

    system = db.query(ExternalSystem).filter(ExternalSystem.id == system_id).first()
    if not system:
        raise HTTPException(status_code=404, detail="外部系统不存在")

    db.delete(system)
    db.commit()

    logger.info(f"用户 {current_user.username} 删除外部系统: {system.name}")

    return {"message": "删除成功"}


@router.get("/{system_id}/access", response_model=ExternalSystemAccess)
def get_system_access(
    system_id: int,
    db: Session = Depends(get_sync_session),
    current_user: User = Depends(get_current_user),
):
    """
    获取外部系统访问令牌
    普通用户可访问自己有权限的系统
    """
    started_at = time.perf_counter()
    system = (
        db.query(ExternalSystem)
        .filter(and_(ExternalSystem.id == system_id, ExternalSystem.is_active == True))
        .first()
    )

    if not system:
        raise HTTPException(status_code=404, detail="外部系统不存在或未启用")

    if not user_can_access_external_system(system, current_user):
        raise HTTPException(status_code=403, detail="没有权限访问该外部系统")

    expires_at = datetime.utcnow() + timedelta(hours=1)
    access_token = generate_access_token(system_id, current_user.id, expires_at)

    duration_ms = int((time.perf_counter() - started_at) * 1000)
    logger.info(
        f"外部系统 access_token 发放成功 user_id={current_user.id} system_id={system_id} duration_ms={duration_ms}"
    )

    return ExternalSystemAccess(
        system_id=system_id,
        user_id=current_user.id,
        access_token=access_token,
        expires_at=expires_at,
    )


@router.post("/{system_id}/access/verify")
def verify_system_access(
    system_id: int, access_token: str, db: Session = Depends(get_sync_session)
):
    """
    验证外部系统访问令牌
    供外部系统调用验证用户权限
    """
    started_at = time.perf_counter()
    system = (
        db.query(ExternalSystem)
        .filter(and_(ExternalSystem.id == system_id, ExternalSystem.is_active == True))
        .first()
    )

    if not system:
        duration_ms = int((time.perf_counter() - started_at) * 1000)
        logger.info(
            f"外部系统 verify 失败 system_id={system_id} reason=system_not_found duration_ms={duration_ms}"
        )
        return {"valid": False}

    try:
        token_data = jwt.decode(
            access_token, settings.secret_key, algorithms=[settings.algorithm]
        )
    except JWTError:
        duration_ms = int((time.perf_counter() - started_at) * 1000)
        logger.info(
            f"外部系统 verify 失败 system_id={system_id} reason=token_invalid duration_ms={duration_ms}"
        )
        return {"valid": False}

    if token_data.get("type") != "external_system_access":
        duration_ms = int((time.perf_counter() - started_at) * 1000)
        logger.info(
            f"外部系统 verify 失败 system_id={system_id} reason=token_type_invalid duration_ms={duration_ms}"
        )
        return {"valid": False}

    if token_data.get("system_id") != system_id:
        duration_ms = int((time.perf_counter() - started_at) * 1000)
        logger.info(
            f"外部系统 verify 失败 system_id={system_id} reason=token_system_mismatch duration_ms={duration_ms}"
        )
        return {"valid": False}

    duration_ms = int((time.perf_counter() - started_at) * 1000)
    logger.info(
        f"外部系统 verify 成功 system_id={system_id} user_id={token_data.get('user_id')} duration_ms={duration_ms}"
    )
    return {
        "valid": True,
        "user_id": token_data.get("user_id"),
        "system_id": system_id,
        "expires_at": datetime.utcfromtimestamp(int(token_data["exp"])).isoformat()
        if token_data.get("exp")
        else None,
    }


@router.get("/{system_id}/integration/config")
def get_integration_config(
    system_id: int,
    integration_type: str = Query(..., pattern="^(iframe|sso|api)$"),
    include_secrets: bool = Query(False),
    db: Session = Depends(get_sync_session),
    current_user: User = Depends(get_current_user),
):
    """
    获取系统集成配置
    用于前端集成外部系统
    """
    system = (
        db.query(ExternalSystem)
        .filter(and_(ExternalSystem.id == system_id, ExternalSystem.is_active == True))
        .first()
    )

    if not system:
        raise HTTPException(status_code=404, detail="外部系统不存在或未启用")

    # 验证用户是否有权限访问此系统
    if not user_can_access_external_system(system, current_user):
        raise HTTPException(status_code=403, detail="没有权限访问该外部系统")

    should_include_secrets = bool(include_secrets and current_user.is_admin)
    safe_config = sanitize_integration_config(
        system.config or {}, should_include_secrets
    )

    config = {
        "system_id": system_id,
        "name": system.name,
        "system_type": system.system_type,
        "integration_type": integration_type,
        "page_url": system.page_url,
        "endpoint_url": system.endpoint_url,
        "config": safe_config,
    }

    # 根据集成类型返回特定配置
    if integration_type == "iframe":
        iframe_config = PageIntegrationConfig(
            url=system.page_url or "",
            width=system.get_config_value("width", "100%"),
            height=system.get_config_value("height", "600px"),
            allow_fullscreen=system.get_config_value("allow_fullscreen", True),
            sandbox=system.get_config_value("sandbox", []),
        )
        config["iframe_config"] = iframe_config.dict()

    elif integration_type == "sso":
        sso_config = SSOIntegrationConfig(
            sso_url=system.get_config_value("sso_url", ""),
            callback_url=system.get_config_value("callback_url", ""),
            client_id=system.get_config_value("client_id", ""),
            client_secret=system.get_config_value("client_secret", "")
            if should_include_secrets
            else "",
            scope=system.get_config_value("scope", "openid profile"),
        )
        config["sso_config"] = sso_config.dict()

    logger.info(f"用户 {current_user.username} 获取外部系统 {system.name} 的集成配置")

    return config


@router.get("/user/accessible")
def get_user_accessible_systems(
    db: Session = Depends(get_sync_session),
    current_user: User = Depends(get_current_user),
):
    """
    获取用户可访问的外部系统列表
    返回用户有权限访问的所有启用系统
    """
    systems = db.query(ExternalSystem).all()

    # 这里可以添加更复杂的权限过滤逻辑
    # 例如基于用户角色、会员等级等

    accessible_systems = []
    for system in systems:
        if not user_can_access_external_system(system, current_user):
            continue

        safe_config = sanitize_integration_config(
            system.config or {}, current_user.is_admin
        )
        default_integration_type = "api" if system.system_type == "api" else "iframe"
        integration_type = system.get_config_value(
            "integration_type", default_integration_type
        )
        system_data = {
            "id": system.id,
            "name": system.name,
            "system_type": system.system_type,
            "page_url": system.page_url,
            "endpoint_url": system.endpoint_url,
            "description": system.get_config_value("description", ""),
            "icon": system.get_config_value("icon", ""),
            "config": safe_config,
            "is_active": system.is_active,
            "integration_type": integration_type,
            "is_page_system": system.is_page_system,
            "is_api_system": system.is_api_system,
        }
        accessible_systems.append(system_data)

    logger.info(
        f"用户 {current_user.username} 查询可访问的外部系统，返回 {len(accessible_systems)} 个系统"
    )

    return {"systems": accessible_systems}
