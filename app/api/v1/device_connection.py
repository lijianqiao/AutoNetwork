"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: device_connection.py
@DateTime: 2025/07/25 21:02:00
@Docs: 设备连接管理API控制器 - 提供设备连接测试、认证管理、连接池管理等RESTful接口
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.core.exceptions import BusinessException
from app.models.user import User
from app.schemas.base import BaseResponse
from app.services.device_connection import DeviceConnectionService
from app.utils.deps import get_current_user
from app.utils.logger import logger

router = APIRouter(prefix="/device-connection", tags=["设备连接管理"])


# 请求模型
class DeviceConnectionTestRequest(BaseModel):
    """设备连接测试请求"""

    device_id: UUID = Field(..., description="设备ID")
    dynamic_password: str | None = Field(None, description="动态密码")


class BatchConnectionTestRequest(BaseModel):
    """批量设备连接测试请求"""

    device_ids: list[UUID] = Field(..., description="设备ID列表")
    dynamic_password: str | None = Field(None, description="统一动态密码（适用于所有动态密码设备）")
    dynamic_passwords: dict[str, str] | None = Field(None, description="设备特定动态密码映射（优先级高于统一密码）")
    max_concurrent: int = Field(20, ge=1, le=50, description="最大并发数")


class ConnectionStabilityTestRequest(BaseModel):
    """连接稳定性测试请求"""

    device_id: UUID = Field(..., description="设备ID")
    duration: int = Field(60, ge=10, le=3600, description="测试持续时间（秒）")
    interval: int = Field(10, ge=5, le=60, description="测试间隔（秒）")


class CredentialsValidationRequest(BaseModel):
    """认证凭据验证请求"""

    device_id: UUID = Field(..., description="设备ID")
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")
    ssh_port: int = Field(22, ge=1, le=65535, description="SSH端口")


class PasswordEncryptionRequest(BaseModel):
    """密码加密请求"""

    password: str = Field(..., description="明文密码")


class DevicesByCriteriaTestRequest(BaseModel):
    """根据条件批量测试设备请求"""

    vendor_id: UUID | None = Field(None, description="厂商ID")
    region_id: UUID | None = Field(None, description="基地ID")
    device_type: str | None = Field(None, description="设备类型")
    network_layer: str | None = Field(None, description="网络层级")
    is_active: bool = Field(True, description="是否活跃")
    max_concurrent: int = Field(20, ge=1, le=50, description="最大并发数")


# 响应模型已移至 app.schemas.base


# 依赖注入
def get_device_connection_service() -> DeviceConnectionService:
    """获取设备连接服务实例"""
    return DeviceConnectionService()


@router.post("/test", response_model=BaseResponse[dict], summary="测试单个设备连接")
async def test_device_connection(
    request: DeviceConnectionTestRequest,
    service: DeviceConnectionService = Depends(get_device_connection_service),
    current_user: User = Depends(get_current_user),
):
    """测试单个设备连接"""
    try:
        logger.info(
            f"用户 {current_user.username} 请求测试设备连接: device_id={request.device_id}, dynamic_password={'*' * len(request.dynamic_password) if request.dynamic_password else 'None'}"
        )

        result = await service.test_device_connection(
            device_id=request.device_id,
            dynamic_password=request.dynamic_password,
        )

        return BaseResponse(data=result, message="设备连接测试完成")

    except BusinessException as e:
        logger.warning(f"设备连接测试业务异常: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(f"设备连接测试系统异常: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="设备连接测试失败",
        ) from e


@router.post("/test/batch", response_model=BaseResponse[dict], summary="批量测试设备连接")
async def test_batch_device_connections(
    request: BatchConnectionTestRequest,
    service: DeviceConnectionService = Depends(get_device_connection_service),
    current_user: User = Depends(get_current_user),
):
    """批量测试设备连接

    支持两种动态密码模式：
    1. 统一动态密码：所有动态密码设备使用同一个密码
    2. 设备特定密码：为特定设备指定不同的密码（优先级更高）
    静态密码设备会自动从数据库获取凭据
    """
    try:
        logger.info(f"用户 {current_user.username} 请求批量测试设备连接，设备数量: {len(request.device_ids)}")

        # 智能处理动态密码映射
        dynamic_passwords = None
        if request.dynamic_passwords or request.dynamic_password:
            dynamic_passwords = {}

            # 如果提供了统一动态密码，先为所有设备设置
            if request.dynamic_password:
                for device_id in request.device_ids:
                    dynamic_passwords[device_id] = request.dynamic_password

            # 如果提供了设备特定密码，覆盖对应设备的密码
            if request.dynamic_passwords:
                for device_id_str, password in request.dynamic_passwords.items():
                    device_id = UUID(device_id_str)
                    if device_id in request.device_ids:
                        dynamic_passwords[device_id] = password

        result = await service.test_batch_device_connections(
            device_ids=request.device_ids,
            dynamic_passwords=dynamic_passwords,
            max_concurrent=request.max_concurrent,
        )

        return BaseResponse(data=result, message="批量设备连接测试完成")

    except BusinessException as e:
        logger.warning(f"批量设备连接测试业务异常: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(f"批量设备连接测试系统异常: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="批量设备连接测试失败",
        ) from e


@router.post("/test/stability", response_model=BaseResponse[dict], summary="测试设备连接稳定性")
async def test_connection_stability(
    request: ConnectionStabilityTestRequest,
    service: DeviceConnectionService = Depends(get_device_connection_service),
    current_user: User = Depends(get_current_user),
):
    """测试设备连接稳定性"""
    try:
        logger.info(f"用户 {current_user.username} 请求测试设备连接稳定性: {request.device_id}")

        result = await service.test_connection_stability(
            device_id=request.device_id,
            duration=request.duration,
            interval=request.interval,
        )

        return BaseResponse(data=result, message="设备连接稳定性测试完成")

    except BusinessException as e:
        logger.warning(f"设备连接稳定性测试业务异常: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(f"设备连接稳定性测试系统异常: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="设备连接稳定性测试失败",
        ) from e


@router.get("/credentials/{device_id}", response_model=BaseResponse[dict], summary="获取设备认证凭据")
async def get_device_credentials(
    device_id: UUID,
    dynamic_password: str | None = Query(None, description="动态密码"),
    service: DeviceConnectionService = Depends(get_device_connection_service),
    current_user: User = Depends(get_current_user),
):
    """获取设备认证凭据"""
    try:
        logger.info(f"用户 {current_user.username} 请求获取设备认证凭据: {device_id}")

        result = await service.get_device_credentials(
            device_id=device_id,
            dynamic_password=dynamic_password,
        )

        return BaseResponse(data=result, message="获取设备认证凭据成功")

    except BusinessException as e:
        logger.warning(f"获取设备认证凭据业务异常: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(f"获取设备认证凭据系统异常: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取设备认证凭据失败",
        ) from e


@router.post("/credentials/validate", response_model=BaseResponse[dict], summary="验证设备认证凭据")
async def validate_device_credentials(
    request: CredentialsValidationRequest,
    service: DeviceConnectionService = Depends(get_device_connection_service),
    current_user: User = Depends(get_current_user),
):
    """验证设备认证凭据"""
    try:
        logger.info(f"用户 {current_user.username} 请求验证设备认证凭据: {request.device_id}")

        result = await service.validate_device_credentials(
            device_id=request.device_id,
            username=request.username,
            password=request.password,
            ssh_port=request.ssh_port,
        )

        return BaseResponse(data=result, message="设备认证凭据验证完成")

    except BusinessException as e:
        logger.warning(f"验证设备认证凭据业务异常: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(f"验证设备认证凭据系统异常: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="验证设备认证凭据失败",
        ) from e


@router.post("/password/encrypt", response_model=BaseResponse[dict], summary="加密设备密码")
async def encrypt_device_password(
    request: PasswordEncryptionRequest,
    service: DeviceConnectionService = Depends(get_device_connection_service),
    current_user: User = Depends(get_current_user),
):
    """加密设备密码"""
    try:
        logger.info(f"用户 {current_user.username} 请求加密设备密码")

        result = await service.encrypt_device_password(request.password)

        return BaseResponse(data=result, message="设备密码加密成功")

    except BusinessException as e:
        logger.warning(f"加密设备密码业务异常: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(f"加密设备密码系统异常: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="加密设备密码失败",
        ) from e


@router.get("/pool/stats", response_model=BaseResponse[dict], summary="获取连接池统计信息")
async def get_connection_pool_stats(
    service: DeviceConnectionService = Depends(get_device_connection_service),
    current_user: User = Depends(get_current_user),
):
    """获取连接池统计信息"""
    try:
        logger.info(f"用户 {current_user.username} 请求获取连接池统计信息")

        result = await service.get_connection_pool_stats()

        return BaseResponse(data=result, message="获取连接池统计信息成功")

    except BusinessException as e:
        logger.warning(f"获取连接池统计信息业务异常: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(f"获取连接池统计信息系统异常: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取连接池统计信息失败",
        ) from e


@router.get("/manager/stats", response_model=BaseResponse[dict], summary="获取连接管理器统计信息")
async def get_connection_manager_stats(
    service: DeviceConnectionService = Depends(get_device_connection_service),
    current_user: User = Depends(get_current_user),
):
    """获取连接管理器统计信息"""
    try:
        logger.info(f"用户 {current_user.username} 请求获取连接管理器统计信息")

        result = await service.get_connection_manager_stats()

        return BaseResponse(data=result, message="获取连接管理器统计信息成功")

    except BusinessException as e:
        logger.warning(f"获取连接管理器统计信息业务异常: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(f"获取连接管理器统计信息系统异常: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取连接管理器统计信息失败",
        ) from e


@router.post("/pool/cleanup", response_model=BaseResponse[dict], summary="清理空闲连接")
async def cleanup_idle_connections(
    idle_timeout: int | None = Query(None, ge=60, le=3600, description="空闲超时时间（秒）"),
    service: DeviceConnectionService = Depends(get_device_connection_service),
    current_user: User = Depends(get_current_user),
):
    """清理空闲连接"""
    try:
        logger.info(f"用户 {current_user.username} 请求清理空闲连接")

        result = await service.cleanup_idle_connections(idle_timeout)

        return BaseResponse(data=result, message="清理空闲连接完成")

    except BusinessException as e:
        logger.warning(f"清理空闲连接业务异常: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(f"清理空闲连接系统异常: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="清理空闲连接失败",
        ) from e


@router.delete("/close/{device_id}", response_model=BaseResponse[dict], summary="关闭设备连接")
async def close_device_connection(
    device_id: UUID,
    service: DeviceConnectionService = Depends(get_device_connection_service),
    current_user: User = Depends(get_current_user),
):
    """关闭指定设备连接"""
    try:
        logger.info(f"用户 {current_user.username} 请求关闭设备连接: {device_id}")

        result = await service.close_device_connection(device_id)

        return BaseResponse(data=result, message="设备连接已关闭")

    except BusinessException as e:
        logger.warning(f"关闭设备连接业务异常: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(f"关闭设备连接系统异常: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="关闭设备连接失败",
        ) from e


@router.post("/pool/start", response_model=BaseResponse[dict], summary="启动连接池")
async def start_connection_pool(
    service: DeviceConnectionService = Depends(get_device_connection_service),
    current_user: User = Depends(get_current_user),
):
    """启动连接池"""
    try:
        logger.info(f"用户 {current_user.username} 请求启动连接池")

        result = await service.start_connection_pool()

        return BaseResponse(data=result, message="连接池已启动")

    except BusinessException as e:
        logger.warning(f"启动连接池业务异常: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(f"启动连接池系统异常: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="启动连接池失败",
        ) from e


@router.post("/pool/stop", response_model=BaseResponse[dict], summary="停止连接池")
async def stop_connection_pool(
    service: DeviceConnectionService = Depends(get_device_connection_service),
    current_user: User = Depends(get_current_user),
):
    """停止连接池"""
    try:
        logger.info(f"用户 {current_user.username} 请求停止连接池")

        result = await service.stop_connection_pool()

        return BaseResponse(data=result, message="连接池已停止")

    except BusinessException as e:
        logger.warning(f"停止连接池业务异常: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(f"停止连接池系统异常: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="停止连接池失败",
        ) from e


@router.post("/test/criteria", response_model=BaseResponse[dict], summary="根据条件批量测试设备")
async def test_devices_by_criteria(
    request: DevicesByCriteriaTestRequest,
    service: DeviceConnectionService = Depends(get_device_connection_service),
    current_user: User = Depends(get_current_user),
):
    """根据条件批量测试设备"""
    try:
        logger.info(f"用户 {current_user.username} 请求根据条件批量测试设备")

        result = await service.test_devices_by_criteria(
            vendor_id=request.vendor_id,
            region_id=request.region_id,
            device_type=request.device_type,
            network_layer=request.network_layer,
            is_active=request.is_active,
            max_concurrent=request.max_concurrent,
        )

        return BaseResponse(data=result, message="根据条件批量测试设备完成")

    except BusinessException as e:
        logger.warning(f"根据条件批量测试设备业务异常: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(f"根据条件批量测试设备系统异常: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="根据条件批量测试设备失败",
        ) from e


@router.delete("/cache/password", response_model=BaseResponse[dict], summary="清除动态密码缓存")
async def clear_dynamic_password_cache(
    device_id: UUID | None = Query(None, description="设备ID，为空则清除所有缓存"),
    service: DeviceConnectionService = Depends(get_device_connection_service),
    current_user: User = Depends(get_current_user),
):
    """清除动态密码缓存"""
    try:
        logger.info(f"用户 {current_user.username} 请求清除动态密码缓存")

        result = service.clear_dynamic_password_cache(device_id)

        return BaseResponse(data=result, message="动态密码缓存已清除")

    except BusinessException as e:
        logger.warning(f"清除动态密码缓存业务异常: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(f"清除动态密码缓存系统异常: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="清除动态密码缓存失败",
        ) from e


@router.get("/cache/password/info", response_model=BaseResponse[dict], summary="获取缓存密码信息")
async def get_cached_password_info(
    service: DeviceConnectionService = Depends(get_device_connection_service),
    current_user: User = Depends(get_current_user),
):
    """获取缓存密码信息"""
    try:
        logger.info(f"用户 {current_user.username} 请求获取缓存密码信息")

        result = service.get_cached_password_info()

        return BaseResponse(data=result, message="获取缓存密码信息成功")

    except BusinessException as e:
        logger.warning(f"获取缓存密码信息业务异常: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(f"获取缓存密码信息系统异常: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取缓存密码信息失败",
        ) from e


@router.get("/statistics", response_model=BaseResponse[dict], summary="获取测试统计信息")
async def get_test_statistics(
    device_ids: list[UUID] | None = Query(None, description="设备ID列表，为空则统计所有设备"),
    service: DeviceConnectionService = Depends(get_device_connection_service),
    current_user: User = Depends(get_current_user),
):
    """获取测试统计信息"""
    try:
        logger.info(f"用户 {current_user.username} 请求获取测试统计信息")

        result = await service.get_test_statistics(device_ids)

        return BaseResponse(data=result, message="获取测试统计信息成功")

    except BusinessException as e:
        logger.warning(f"获取测试统计信息业务异常: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(f"获取测试统计信息系统异常: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取测试统计信息失败",
        ) from e
