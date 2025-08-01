"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: device_connection.py
@DateTime: 2025/07/25 21:02:00
@Docs: 设备连接与认证管理API控制器 - 提供设备连接测试、认证管理、连接池管理等RESTful接口
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.exceptions import BusinessException
from app.models.user import User
from app.schemas.authentication import (
    AuthenticationConfigInfo,
    AuthenticationTestRequest,
    AuthenticationTestResult,
    BatchAuthenticationTestRequest,
    BatchAuthenticationTestResult,
    DeviceCredentialsRequest,
    DeviceCredentialsResponse,
    UsernameGenerationRequest,
    UsernameGenerationResult,
)
from app.schemas.base import BaseResponse, SuccessResponse
from app.schemas.device_connection import (
    BatchConnectionTestRequest,
    ConnectionStabilityTestRequest,
    CredentialsValidationRequest,
    DeviceConnectionTestRequest,
    DevicesByCriteriaTestRequest,
    PasswordEncryptionRequest,
)
from app.services.authentication import AuthenticationManager
from app.services.device_connection import DeviceConnectionService
from app.utils.deps import get_current_user
from app.utils.logger import logger

router = APIRouter(prefix="/device-connection", tags=["设备连接与认证管理"])


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


@router.delete("/cache/password/clear", response_model=SuccessResponse, summary="清除动态密码缓存（统一接口）")
async def clear_dynamic_password_cache_unified(
    device_id: UUID | None = Query(None, description="设备ID，为空则清除所有缓存"),
    service: DeviceConnectionService = Depends(get_device_connection_service),
    current_user: User = Depends(get_current_user),
):
    """清除动态密码缓存（统一接口）

    这是统一的动态密码缓存清除接口，整合了原来的两个接口：
    - /cache/password (原DeviceConnectionService)
    - /auth/cache/clear (原AuthenticationManager)
    """
    try:
        logger.info(f"用户 {current_user.username} 请求清除动态密码缓存")

        # 使用DeviceConnectionService的方法
        service.clear_dynamic_password_cache(device_id)

        # 也清除AuthenticationManager的缓存
        auth_manager = AuthenticationManager()
        auth_manager.clear_dynamic_password_cache(device_id)

        if device_id:
            message = f"已清除设备 {device_id} 的动态密码缓存"
        else:
            message = "已清除所有动态密码缓存"

        return SuccessResponse(message=message)

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


@router.get("/cache/password/info/unified", response_model=BaseResponse[dict], summary="获取缓存密码信息（统一接口）")
async def get_cached_password_info_unified(
    service: DeviceConnectionService = Depends(get_device_connection_service),
    current_user: User = Depends(get_current_user),
):
    """获取缓存密码信息（统一接口）

    这是统一的缓存密码信息获取接口，整合了原来的两个接口：
    - /cache/password/info (原DeviceConnectionService)
    - /auth/cache/info (原AuthenticationManager)
    """
    try:
        logger.info(f"用户 {current_user.username} 请求获取缓存密码信息")

        # 获取DeviceConnectionService的缓存信息
        device_connection_result = service.get_cached_password_info()

        # 获取AuthenticationManager的缓存信息
        auth_manager = AuthenticationManager()
        auth_cached_count = auth_manager.get_cached_password_count()

        unified_result = {
            "device_connection_cache": device_connection_result,
            "authentication_cache": {
                "cached_count": auth_cached_count,
                "message": f"当前缓存了 {auth_cached_count} 个动态密码",
            },
            "total_cached_count": auth_cached_count,
            "message": "获取缓存密码信息成功",
        }

        return BaseResponse(data=unified_result, message="获取缓存密码信息成功")

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


# ===== 设备认证管理功能 =====


@router.post("/auth/credentials", response_model=BaseResponse[DeviceCredentialsResponse], summary="获取设备认证凭据")
async def get_device_auth_credentials(
    request: DeviceCredentialsRequest,
    current_user: User = Depends(get_current_user),
):
    """获取设备认证凭据

    支持动态密码（用户手动输入）和静态密码（数据库获取）两种认证方式。
    对于动态密码认证的设备，需要在请求中提供dynamic_password参数。
    """
    logger.info(f"用户 {current_user.username} 请求获取设备认证凭据: device_id={request.device_id}")

    auth_manager = AuthenticationManager()

    try:
        # 获取认证凭据
        credentials = await auth_manager.get_device_credentials(
            device_id=request.device_id, dynamic_password=request.dynamic_password
        )

        # 获取设备信息用于响应
        device = await auth_manager.device_dao.get_by_id(request.device_id)
        if not device:
            raise Exception("设备不存在")

        region = await device.region
        vendor = await device.vendor

        credentials_data = DeviceCredentialsResponse(
            device_id=str(device.id),
            hostname=device.hostname,
            ip_address=device.ip_address,
            auth_type=device.auth_type,
            username=credentials.username,
            has_password=bool(credentials.password),
            has_snmp_community=bool(credentials.snmp_community),
            ssh_port=credentials.ssh_port,
            region_code=region.region_code if region else "",
            vendor_code=vendor.vendor_code if vendor else "",
            scrapli_platform=vendor.scrapli_platform if vendor else "",
        )

        return BaseResponse(data=credentials_data, message="获取设备认证凭据成功")

    except Exception as e:
        logger.error(f"获取设备认证凭据失败: device_id={request.device_id}, error={e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e


@router.post("/auth/test", response_model=BaseResponse[AuthenticationTestResult], summary="测试设备认证")
async def test_device_authentication(
    request: AuthenticationTestRequest,
    current_user: User = Depends(get_current_user),
):
    """测试设备认证

    验证设备的认证凭据是否正确配置，但不实际连接设备。
    主要用于检查认证配置的完整性和有效性。
    """
    logger.info(f"用户 {current_user.username} 请求测试设备认证: device_id={request.device_id}")

    auth_manager = AuthenticationManager()

    try:
        # 获取设备信息
        device = await auth_manager.device_dao.get_by_id(request.device_id)
        if not device:
            raise Exception("设备不存在")

        region = await device.region
        vendor = await device.vendor

        # 获取认证凭据
        credentials = await auth_manager.get_device_credentials(
            device_id=request.device_id, dynamic_password=request.dynamic_password
        )

        # 验证凭据
        is_valid = await auth_manager.validate_device_credentials(request.device_id, credentials)

        result = AuthenticationTestResult(
            success=is_valid,
            device_id=str(device.id),
            hostname=device.hostname,
            ip_address=device.ip_address,
            auth_type=device.auth_type,
            username=credentials.username,
            has_password=bool(credentials.password),
            has_snmp_community=bool(credentials.snmp_community),
            ssh_port=credentials.ssh_port,
            credentials_valid=is_valid,
            region_code=region.region_code if region else "",
            vendor_code=vendor.vendor_code if vendor else "",
            scrapli_platform=vendor.scrapli_platform if vendor else "",
            error=None if is_valid else "认证凭据验证失败",
            message="认证测试完成",
        )

        return BaseResponse(data=result, message="认证测试完成")

    except Exception as e:
        logger.error(f"测试设备认证失败: device_id={request.device_id}, error={e}")

        result = AuthenticationTestResult(
            success=False, device_id=str(request.device_id), error=str(e), message="认证测试失败"
        )
        return BaseResponse(data=result, message="认证测试失败")


@router.post("/auth/test/batch", response_model=BaseResponse[BatchAuthenticationTestResult], summary="批量测试设备认证")
async def batch_test_device_authentication(
    request: BatchAuthenticationTestRequest,
    current_user: User = Depends(get_current_user),
):
    """批量测试设备认证

    对多个设备进行认证测试，支持为不同设备提供不同的动态密码。
    """
    logger.info(f"用户 {current_user.username} 请求批量测试设备认证: 设备数量={len(request.device_ids)}")

    auth_manager = AuthenticationManager()
    results = []
    success_count = 0
    failed_count = 0

    for device_id in request.device_ids:
        try:
            # 获取该设备的动态密码
            dynamic_password = None
            if request.dynamic_passwords:
                dynamic_password = request.dynamic_passwords.get(str(device_id))

            # 获取设备信息
            device = await auth_manager.device_dao.get_by_id(device_id)
            if not device:
                raise Exception("设备不存在")

            region = await device.region
            vendor = await device.vendor

            # 获取认证凭据
            credentials = await auth_manager.get_device_credentials(
                device_id=device_id, dynamic_password=dynamic_password
            )

            # 验证凭据
            is_valid = await auth_manager.validate_device_credentials(device_id, credentials)

            result = AuthenticationTestResult(
                success=is_valid,
                device_id=str(device.id),
                hostname=device.hostname,
                ip_address=device.ip_address,
                auth_type=device.auth_type,
                username=credentials.username,
                has_password=bool(credentials.password),
                has_snmp_community=bool(credentials.snmp_community),
                ssh_port=credentials.ssh_port,
                credentials_valid=is_valid,
                region_code=region.region_code if region else "",
                vendor_code=vendor.vendor_code if vendor else "",
                scrapli_platform=vendor.scrapli_platform if vendor else "",
                error=None if is_valid else "认证凭据验证失败",
                message="认证测试完成",
            )

            results.append(result)

            if result.success:
                success_count += 1
            else:
                failed_count += 1

        except Exception as e:
            logger.error(f"批量测试中设备认证失败: device_id={device_id}, error={e}")

            error_result = AuthenticationTestResult(
                success=False, device_id=str(device_id), error=str(e), message="认证测试异常"
            )
            results.append(error_result)
            failed_count += 1

    total_count = len(request.device_ids)
    summary = f"总计 {total_count} 个设备，成功 {success_count} 个，失败 {failed_count} 个"

    batch_result = BatchAuthenticationTestResult(
        total_count=total_count,
        success_count=success_count,
        failed_count=failed_count,
        results=results,
        summary=summary,
    )

    return BaseResponse(
        data=batch_result,
        message="批量认证测试完成",
    )


@router.post("/auth/username/generate", response_model=BaseResponse[UsernameGenerationResult], summary="生成动态用户名")
async def generate_dynamic_username(
    request: UsernameGenerationRequest,
    current_user: User = Depends(get_current_user),
):
    """生成动态用户名

    根据网络层级和基地代码生成符合规则的用户名。
    """
    logger.info(
        f"用户 {current_user.username} 请求生成动态用户名: layer={request.network_layer}, region={request.region_code}"
    )

    auth_manager = AuthenticationManager()

    # 获取用户名模式
    pattern = auth_manager.username_patterns.get(request.network_layer, "{region_code}_{network_layer}_admin")

    # 生成用户名
    username = pattern.format(region_code=request.region_code.lower(), network_layer=request.network_layer)

    result = UsernameGenerationResult(
        network_layer=request.network_layer,
        region_code=request.region_code,
        generated_username=username,
        pattern_used=pattern,
    )

    return BaseResponse(
        data=result,
        message="用户名生成成功",
    )


@router.get("/auth/config", response_model=BaseResponse[AuthenticationConfigInfo], summary="获取认证配置信息")
async def get_authentication_config(
    current_user: User = Depends(get_current_user),
):
    """获取认证配置信息

    返回认证系统的配置信息，包括用户名生成模式、支持的认证类型等。
    """
    logger.debug(f"用户 {current_user.username} 请求获取认证配置信息")

    auth_manager = AuthenticationManager()
    cached_count = auth_manager.get_cached_password_count()

    config_info = AuthenticationConfigInfo(
        username_patterns=auth_manager.username_patterns,
        supported_auth_types=["dynamic", "static"],
        dynamic_password_cache_enabled=True,
        current_cached_count=cached_count,
    )

    return BaseResponse(
        data=config_info,
        message="获取认证配置成功",
    )
