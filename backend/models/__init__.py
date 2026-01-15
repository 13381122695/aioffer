# 数据模型模块
from .user import User, UserAuth, EmailVerificationCode, LoginLog
from .member import Member
from .role import Role, Permission, user_roles, role_permissions
from .menu import Menu
from .order import Order
from .point import PointTransaction
from .external_system import ExternalSystem
from .system_config import SystemConfig

# 初始化用户角色关系
from .role import init_user_role_relationship

init_user_role_relationship()

__all__ = [
    "User",
    "UserAuth",
    "EmailVerificationCode",
    "LoginLog",
    "Member",
    "Role",
    "Permission",
    "user_roles",
    "role_permissions",
    "Menu",
    "Order",
    "PointTransaction",
    "ExternalSystem",
    "SystemConfig",
]
