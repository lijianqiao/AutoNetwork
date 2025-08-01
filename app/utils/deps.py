"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: deps.py
@DateTime: 2025/07/10
@Docs: FastAPI依赖注入
"""

from typing import NamedTuple

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer

from app.core.config import settings
from app.core.exceptions import UnauthorizedException
from app.core.security import SecurityManager, security_manager
from app.models.user import User
from app.schemas.auth import TokenPayload

# 移除直接导入，改为延迟导入
from app.utils import logger

reusable_oauth2 = OAuth2PasswordBearer(tokenUrl=f"{settings.API_PREFIX}/v1/auth/login/form")


# ==================== 服务依赖 ====================
def get_user_service():
    from app.services.user import UserService

    return UserService()


def get_role_service():
    from app.services.role import RoleService

    return RoleService()


def get_permission_service():
    from app.services.permission import PermissionService

    return PermissionService()


def get_auth_service():
    from app.services.auth import AuthService

    return AuthService()


def get_operation_log_service():
    from app.services.operation_log import OperationLogService

    return OperationLogService()


def get_device_service():
    from app.services.device import DeviceService

    return DeviceService()


def get_vendor_command_service():
    from app.services.vendor_command import VendorCommandService

    return VendorCommandService()


def get_query_history_service():
    from app.services.query_history import QueryHistoryService

    return QueryHistoryService()


def get_query_template_service():
    from app.services.query_template import QueryTemplateService

    return QueryTemplateService()


def get_region_service():
    from app.services.region import RegionService

    return RegionService()


def get_vendor_service():
    from app.services.vendor import VendorService

    return VendorService()


def get_device_config_service():
    from app.services.device_config import DeviceConfigService

    return DeviceConfigService()


def get_import_export_service():
    from app.services.import_export import ImportExportService

    return ImportExportService()


def get_network_query_service():
    from app.services.network_query import NetworkQueryService

    return NetworkQueryService()


def get_universal_query_service():
    from app.services.universal_query import UniversalQueryService

    return UniversalQueryService()


def get_device_connection_service():
    from app.services.device_connection import DeviceConnectionService

    return DeviceConnectionService()


def get_cli_service():
    from app.services.cli_session import CLISessionService

    return CLISessionService()


def get_security_manager() -> SecurityManager:
    return security_manager


def get_statistics_service():
    from app.services.statistics import StatisticsService

    return StatisticsService()


# ==================== 用户依赖 ====================
async def get_current_user(token: str = Depends(reusable_oauth2), user_service=Depends(get_user_service)) -> User:
    """通过JWT令牌获取当前用户模型"""

    try:
        payload = security_manager.verify_token(token, "access")
        token_data = TokenPayload.model_validate(payload)

        user = await user_service.get_by_id(token_data.sub)
        if not user:
            logger.error("用户不存在")
            raise UnauthorizedException(detail="用户不存在")
        logger.debug(f"[DEBUG] 用户认证成功: {user.username}")
        return user
    except Exception as e:
        logger.error(f" get_current_user异常: {type(e).__name__}: {str(e)}")
        raise


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """获取当前活跃用户"""
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="用户已被禁用")
    return current_user


async def get_current_superuser(current_user: User = Depends(get_current_active_user)) -> User:
    """获取当前超级用户"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权操作，需要超级管理员权限")
    return current_user


# ==================== 操作日志依赖 ====================
class OperationContext(NamedTuple):
    """操作上下文 - 用于操作日志记录"""

    user: User
    request: Request | None


async def get_operation_context(
    request: Request, current_user: User = Depends(get_current_active_user)
) -> OperationContext:
    """获取操作上下文，包含用户和请求信息"""
    return OperationContext(user=current_user, request=request)
