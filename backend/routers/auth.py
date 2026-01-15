"""
认证路由
创建日期: 2025-01-08
用途: 用户登录、注册、刷新令牌等认证功能
"""

from datetime import datetime, timedelta
import hashlib
import hmac
import secrets
import smtplib
from email.headerregistry import Address
from email.message import EmailMessage
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, update, func
from sqlalchemy.orm import selectinload

from config import get_async_session, settings
from models import User, UserAuth, EmailVerificationCode, LoginLog, Member
from schemas import (
    LoginRequest,
    TokenResponse,
    RegisterRequest,
    ChangePasswordRequest,
    SendEmailCodeRequest,
)
from utils.security import SecurityManager
from utils.response import success, error, unauthorized
from utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")


def build_login_user_payload(user: User) -> dict:
    role = "admin" if user.is_admin else ("member" if user.is_member else "user")
    points = None
    if getattr(user, "member", None):
        points = user.member.points
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email or "",
        "phone": user.phone,
        "avatar": user.avatar_url,
        "role": role,
        "is_active": user.is_active,
        "points": points,
        "created_at": user.created_at,
        "updated_at": user.updated_at,
    }


def get_client_ip(request: Request) -> str | None:
    for header_name in (
        "cf-connecting-ip",
        "true-client-ip",
        "x-real-ip",
    ):
        value = request.headers.get(header_name)
        if value:
            return value.strip()

    x_forwarded_for = request.headers.get("x-forwarded-for")
    if x_forwarded_for:
        parts = [p.strip() for p in x_forwarded_for.split(",") if p.strip()]
        if parts:
            return parts[0]

    forwarded = request.headers.get("forwarded")
    if forwarded:
        segments = [s.strip() for s in forwarded.split(",") if s.strip()]
        for segment in segments:
            items = [i.strip() for i in segment.split(";") if i.strip()]
            for item in items:
                if item.lower().startswith("for="):
                    value = item[4:].strip().strip('"')
                    if value.startswith("[") and "]" in value:
                        value = value[1 : value.index("]")]
                    if ":" in value and value.count(":") == 1:
                        value = value.split(":", 1)[0]
                    if value:
                        return value

    if request.client:
        return request.client.host
    return None


def mask_email(value: str) -> str:
    if "@" not in value:
        return "***"
    local, domain = value.split("@", 1)
    if not local:
        return f"***@{domain}"
    if len(local) == 1:
        return f"{local}***@{domain}"
    return f"{local[0]}***{local[-1]}@{domain}"


def hash_email_code(email: str, code: str) -> str:
    message = f"{email}:{code}".encode("utf-8")
    secret = (settings.secret_key or "").encode("utf-8")
    return hmac.new(secret, message, hashlib.sha256).hexdigest()


def get_email_purpose_text(purpose: str) -> str:
    purpose_map = {
        "register": "注册",
        "reset_password": "找回密码",
        "change_email": "变更邮箱",
    }
    return purpose_map.get(purpose, "验证")


def build_email_code_messages(
    *, code: str, expire_minutes: int, purpose: str
) -> tuple[str, str, str]:
    product_name = settings.email_product_name or ""
    purpose_text = get_email_purpose_text(purpose)
    subject = (
        f"【{product_name}】{purpose_text}验证码：{code}"
        if product_name
        else f"{purpose_text}验证码：{code}"
    )

    text_body = f"您的{purpose_text}验证码是：{code}\n\n" f"验证码 {expire_minutes} 分钟内有效，请勿泄露。\n"

    html_body = f"""
<html>
  <body>
    <p>您好！</p>
    <p>{product_name}向您发送的{purpose_text}验证码为：<strong style="color: #d32f2f; font-size: 24px;">{code}</strong></p>
    <p>该验证码{expire_minutes}分钟内有效，请勿泄露给他人。</p>
    <p>—— {product_name}自动发送，请勿回复</p>
  </body>
</html>
""".strip()

    return subject, text_body, html_body


def send_email_code_smtp(
    to_email: str, code: str, expire_minutes: int, purpose: str
) -> None:
    if not settings.smtp_host or not settings.smtp_user or not settings.smtp_password:
        raise RuntimeError("SMTP未配置")

    from_email = settings.email_from or settings.smtp_user
    subject, text_body, html_body = build_email_code_messages(
        code=code, expire_minutes=expire_minutes, purpose=purpose
    )
    msg = EmailMessage()
    msg["Subject"] = subject

    if settings.email_from_name and "@" in from_email:
        username, domain = from_email.split("@", 1)
        msg["From"] = str(
            Address(
                display_name=settings.email_from_name, username=username, domain=domain
            )
        )
    else:
        msg["From"] = from_email

    msg["To"] = to_email
    msg.set_content(text_body)
    msg.add_alternative(html_body, subtype="html")

    if settings.smtp_use_ssl:
        with smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port) as server:
            server.login(settings.smtp_user, settings.smtp_password)
            server.send_message(msg, from_addr=from_email, to_addrs=[to_email])
        return

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
        if settings.smtp_use_tls:
            server.starttls()
        server.login(settings.smtp_user, settings.smtp_password)
        server.send_message(msg, from_addr=from_email, to_addrs=[to_email])


async def save_login_log(
    db: AsyncSession,
    http_request: Request,
    *,
    user: User | None,
    auth_type: str,
    identifier: str | None,
    success_flag: bool,
    failure_reason: str | None,
) -> None:
    try:
        db.add(
            LoginLog(
                user_id=user.id if user else None,
                auth_type=auth_type,
                identifier=identifier,
                ip=get_client_ip(http_request),
                user_agent=http_request.headers.get("user-agent"),
                success=success_flag,
                failure_reason=failure_reason,
            )
        )
        await db.commit()
    except Exception:
        await db.rollback()


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_async_session)
) -> User:
    """获取当前用户"""
    try:
        print(f"DEBUG: get_current_user called. Token: {token[:10]}...")
        payload = SecurityManager.verify_access_token(token)
        user_id = int(payload.get("sub"))
        if not user_id:
            raise HTTPException(status_code=401, detail="无效的认证令牌")

        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user or not user.is_active:
            raise HTTPException(status_code=401, detail="用户不存在或已被禁用")

        return user
    except Exception as e:
        logger.error(f"获取当前用户失败: {str(e)}")
        print(f"DEBUG: get_current_user ERROR: {e}")
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=401, detail="认证失败")


@router.post("/send-email-code", summary="发送邮箱验证码")
async def send_email_code(
    request: SendEmailCodeRequest,
    background_tasks: BackgroundTasks,
    http_request: Request,
    db: AsyncSession = Depends(get_async_session),
):
    """发送邮箱验证码"""
    if not settings.smtp_host or not settings.smtp_user or not settings.smtp_password:
        return error("邮件服务未配置")

    try:
        email = str(request.email).strip().lower()
        purpose = (request.purpose or "register").strip().lower()
        if purpose not in {"register", "reset_password", "change_email"}:
            return error("不支持的验证码用途")

        client_ip = get_client_ip(http_request)
        logger.info(
            f"email_code_send_requested email={mask_email(email)} purpose={purpose} ip={client_ip}"
        )

        result = await db.execute(select(User).where(User.email == email))
        user_exists = result.scalar_one_or_none() is not None
        if purpose == "register" and user_exists:
            return error("邮箱已存在")
        if purpose in {"reset_password", "change_email"} and not user_exists:
            return error("邮箱不存在")

        now = datetime.now()
        resend_interval_seconds = max(
            int(settings.email_code_resend_interval_seconds), 0
        )

        last_sent_query = select(func.max(EmailVerificationCode.created_at)).where(
            and_(
                EmailVerificationCode.email == email,
                EmailVerificationCode.purpose == purpose,
            )
        )
        last_sent_at = (await db.execute(last_sent_query)).scalar_one_or_none()
        if last_sent_at and resend_interval_seconds > 0:
            delta_seconds = int((now - last_sent_at).total_seconds())
            if delta_seconds < resend_interval_seconds:
                logger.info(
                    f"email_code_send_rejected reason=resend_too_fast email={mask_email(email)} purpose={purpose} ip={client_ip}"
                )
                return error("操作过于频繁，请稍后再试")

        day_start = datetime(now.year, now.month, now.day)
        email_daily_limit = max(int(settings.email_code_daily_limit_per_email), 0)
        ip_daily_limit = max(int(settings.email_code_daily_limit_per_ip), 0)

        if email_daily_limit > 0:
            email_count_query = (
                select(func.count())
                .select_from(EmailVerificationCode)
                .where(
                    and_(
                        EmailVerificationCode.email == email,
                        EmailVerificationCode.purpose == purpose,
                        EmailVerificationCode.created_at >= day_start,
                    )
                )
            )
            email_count_today = int(
                (await db.execute(email_count_query)).scalar_one() or 0
            )
            if email_count_today >= email_daily_limit:
                logger.info(
                    f"email_code_send_rejected reason=email_daily_limit email={mask_email(email)} purpose={purpose} ip={client_ip}"
                )
                return error("操作过于频繁，请稍后再试")

        if client_ip and ip_daily_limit > 0:
            ip_count_query = (
                select(func.count())
                .select_from(EmailVerificationCode)
                .where(
                    and_(
                        EmailVerificationCode.ip == client_ip,
                        EmailVerificationCode.created_at >= day_start,
                    )
                )
            )
            ip_count_today = int((await db.execute(ip_count_query)).scalar_one() or 0)
            if ip_count_today >= ip_daily_limit:
                logger.info(
                    f"email_code_send_rejected reason=ip_daily_limit email={mask_email(email)} purpose={purpose} ip={client_ip}"
                )
                return error("操作过于频繁，请稍后再试")

        await db.execute(
            update(EmailVerificationCode)
            .where(
                and_(
                    EmailVerificationCode.email == email,
                    EmailVerificationCode.purpose == purpose,
                    EmailVerificationCode.used_at.is_(None),
                )
            )
            .values(used_at=now)
        )

        code_length = max(int(settings.email_code_length), 4)
        max_number = 10**code_length
        code = f"{secrets.randbelow(max_number):0{code_length}d}"
        expire_minutes = settings.email_code_expire_minutes
        expires_at = now + timedelta(minutes=expire_minutes)

        db.add(
            EmailVerificationCode(
                email=email,
                purpose=purpose,
                code_hash=hash_email_code(email, code),
                expires_at=expires_at,
                ip=client_ip,
                user_agent=http_request.headers.get("user-agent"),
                created_at=now,
            )
        )
        await db.commit()

        background_tasks.add_task(
            send_email_code_smtp, email, code, expire_minutes, purpose
        )
        logger.info(
            f"email_code_send_enqueued email={mask_email(email)} purpose={purpose} ip={client_ip}"
        )
        return success(None, "验证码已发送")
    except Exception as e:
        await db.rollback()
        logger.error(f"发送邮箱验证码失败: {str(e)}")
        return error("发送验证码失败，请稍后重试")


@router.post("/register", summary="用户注册")
async def register(
    request: RegisterRequest, db: AsyncSession = Depends(get_async_session)
):
    """用户注册"""
    try:
        if request.auth_type != "email":
            return error("仅支持邮箱注册")

        if not request.email or not request.password or not request.email_code:
            return error("邮箱、密码、验证码不能为空")

        now = datetime.now()

        result = await db.execute(
            select(EmailVerificationCode)
            .where(
                and_(
                    EmailVerificationCode.email == request.email,
                    EmailVerificationCode.purpose == "register",
                    EmailVerificationCode.used_at.is_(None),
                )
            )
            .order_by(EmailVerificationCode.id.desc())
            .limit(1)
        )
        code_row = result.scalar_one_or_none()
        if not code_row or code_row.expires_at <= now:
            return error("验证码已过期，请重新获取")

        if not hmac.compare_digest(
            code_row.code_hash, hash_email_code(request.email, request.email_code)
        ):
            return error("验证码错误")

        # 检查用户名是否已存在
        result = await db.execute(select(User).where(User.username == request.username))
        if result.scalar_one_or_none():
            return error("用户名已存在")

        # 检查邮箱是否已存在（如果提供了邮箱）
        if request.email:
            result = await db.execute(select(User).where(User.email == request.email))
            if result.scalar_one_or_none():
                return error("邮箱已存在")

        # 创建用户
        user_data = {
            "username": request.username,
            "email": request.email,
            "full_name": request.full_name,
            "phone": None,
            "status": 1,
            "user_type": 2,
        }

        # 如果有密码，设置密码
        if request.password:
            user_data["password_hash"] = SecurityManager.hash_password(request.password)

        user = User(**user_data)
        db.add(user)
        await db.flush()

        member = Member(user_id=user.id, points=3, balance=0.00)
        db.add(member)

        # 创建用户认证记录
        user_auth = UserAuth(
            user_id=user.id,
            auth_type="email",
            auth_key=request.email,
            auth_secret=user.password_hash,
            is_verified=True,
            verified_at=datetime.now(),
        )
        db.add(user_auth)

        code_row.used_at = now

        await db.commit()

        logger.info(f"用户注册成功: {user.username}")
        return success({"user_id": user.id, "username": user.username}, "注册成功")

    except Exception as e:
        await db.rollback()
        logger.error(f"用户注册失败: {str(e)}")
        return error("注册失败，请稍后重试")


@router.post("/login", summary="用户登录")
async def login(
    request: LoginRequest,
    http_request: Request,
    db: AsyncSession = Depends(get_async_session),
):
    """用户登录（支持多种方式）"""
    try:
        user = None
        failure_reason = None
        identifier = None

        if request.auth_type == "email":
            if not request.email or not request.password:
                failure_reason = "邮箱和密码不能为空"
            identifier = request.email

            # 邮箱登录
            if not failure_reason:
                result = await db.execute(
                    select(User)
                    .join(UserAuth)
                    .where(
                        and_(
                            UserAuth.auth_type == "email",
                            UserAuth.auth_key == request.email,
                            UserAuth.is_verified == True,
                        )
                    )
                    .options(selectinload(User.member))
                )
                user = result.scalar_one_or_none()

            if not failure_reason and (not user or not user.password_hash):
                failure_reason = "邮箱或密码错误"

            if not failure_reason and not SecurityManager.verify_password(
                request.password, user.password_hash
            ):
                failure_reason = "邮箱或密码错误"

        elif request.auth_type == "username":
            if not request.username or not request.password:
                failure_reason = "用户名和密码不能为空"
            identifier = request.username

            # 用户名登录
            if not failure_reason:
                result = await db.execute(
                    select(User)
                    .where(User.username == request.username)
                    .options(selectinload(User.member))
                )
                user = result.scalar_one_or_none()

            if not failure_reason and (not user or not user.password_hash):
                failure_reason = "用户名或密码错误"

            if not failure_reason and not SecurityManager.verify_password(
                request.password, user.password_hash
            ):
                failure_reason = "用户名或密码错误"

        else:
            failure_reason = "不支持的登录方式"

        if not failure_reason and (not user or not user.is_active):
            failure_reason = "账号不存在或已被禁用"

        if failure_reason:
            await save_login_log(
                db,
                http_request,
                user=user,
                auth_type=request.auth_type,
                identifier=identifier,
                success_flag=False,
                failure_reason=failure_reason,
            )
            return error(failure_reason)

        # 生成令牌
        tokens = SecurityManager.create_tokens(user.id, user.username)

        await save_login_log(
            db,
            http_request,
            user=user,
            auth_type=request.auth_type,
            identifier=identifier,
            success_flag=True,
            failure_reason=None,
        )

        logger.info(f"用户登录成功: {user.username}")
        return success({**tokens, "user": build_login_user_payload(user)}, "登录成功")

    except Exception as e:
        await save_login_log(
            db,
            http_request,
            user=None,
            auth_type=request.auth_type,
            identifier=request.email or request.username,
            success_flag=False,
            failure_reason="登录异常",
        )
        logger.error(f"用户登录失败: {str(e)}")
        return error("登录失败，请稍后重试")


@router.post("/logout", summary="用户登出")
async def logout(current_user: User = Depends(get_current_user)):
    """用户登出"""
    logger.info(f"用户登出: {current_user.username}")
    return success(None, "登出成功")


@router.post("/refresh", summary="刷新访问令牌")
async def refresh_token(
    refresh_token: str, db: AsyncSession = Depends(get_async_session)
):
    """刷新访问令牌"""
    try:
        # 验证刷新令牌
        payload = SecurityManager.verify_refresh_token(refresh_token)
        user_id = int(payload.get("sub"))
        username = payload.get("username")

        if not user_id or not username:
            return unauthorized("无效的刷新令牌")

        # 检查用户是否存在
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user or not user.is_active:
            return unauthorized("用户不存在或已被禁用")

        # 生成新的访问令牌
        new_access_token = SecurityManager.refresh_access_token(refresh_token)

        return success(
            {
                "access_token": new_access_token,
                "token_type": "bearer",
                "expires_in": settings.access_token_expire_minutes * 60,
            },
            "令牌刷新成功",
        )

    except Exception as e:
        logger.error(f"刷新令牌失败: {str(e)}")
        return unauthorized("刷新令牌失败")


@router.get("/profile", summary="获取用户信息")
async def get_profile(current_user: User = Depends(get_current_user)):
    """获取用户信息"""
    return success(
        {
            "id": current_user.id,
            "username": current_user.username,
            "email": current_user.email,
            "full_name": current_user.full_name,
            "avatar_url": current_user.avatar_url,
            "phone": current_user.phone,
            "status": current_user.status,
            "user_type": current_user.user_type,
            "is_active": current_user.is_active,
            "is_admin": current_user.is_admin,
            "is_member": current_user.is_member,
            "created_at": current_user.created_at,
            "updated_at": current_user.updated_at,
        }
    )


@router.put("/profile", summary="更新用户信息")
async def update_profile(
    request: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """更新用户信息"""
    try:
        # 只允许更新部分字段
        allowed_fields = ["email", "full_name", "avatar_url", "phone"]

        for field in allowed_fields:
            if field in request and request[field] is not None:
                setattr(current_user, field, request[field])

        await db.commit()

        logger.info(f"用户更新信息成功: {current_user.username}")
        return success(None, "更新成功")

    except Exception as e:
        await db.rollback()
        logger.error(f"用户更新信息失败: {str(e)}")
        return error("更新失败")


@router.post("/change-password", summary="修改密码")
async def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """修改密码"""
    try:
        if not current_user.password_hash:
            return error("当前用户未设置密码")

        # 验证旧密码
        if not SecurityManager.verify_password(
            request.old_password, current_user.password_hash
        ):
            return error("旧密码错误")

        # 设置新密码
        current_user.password_hash = SecurityManager.hash_password(request.new_password)

        await db.commit()

        logger.info(f"用户修改密码成功: {current_user.username}")
        return success(None, "密码修改成功")

    except Exception as e:
        await db.rollback()
        logger.error(f"用户修改密码失败: {str(e)}")
        return error("密码修改失败")
