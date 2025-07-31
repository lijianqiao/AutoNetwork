"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: authentication.py
@DateTime: 2025/07/23
@Docs: 设备认证管理API端点
"""

from fastapi import APIRouter, Depends

from app.core.permissions.simple_decorators import require_permission
from app.models.user import User
from app.schemas.authentication import (
    AuthenticationConfigInfo,
    AuthenticationTestRequest,
    AuthenticationTestResult,
    BatchAuthenticationTestRequest,
    BatchAuthenticationTestResult,
    DeviceCredentialsRequest,
    DeviceCredentialsResponse,
    DynamicPasswordCacheInfo,
    DynamicPasswordClearRequest,
    UsernameGenerationRequest,
    UsernameGenerationResult,
)
from app.schemas.base import BaseResponse, SuccessResponse
from app.services.authentication import AuthenticationManager
from app.utils.deps import get_current_active_user
from app.utils.logger import logger

router = APIRouter(prefix="/authentication", tags=["设备认证管理"])


@router.post(
    "/credentials",
    response_model=BaseResponse[DeviceCredentialsResponse],
    summary="获取设备认证凭据",
    dependencies=[Depends(require_permission("device:read"))],
)
async def get_device_credentials(
    request: DeviceCredentialsRequest,
    current_user: User = Depends(get_current_active_user),
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
        raise


@router.post(
    "/test",
    response_model=BaseResponse[AuthenticationTestResult],
    summary="测试设备认证",
    dependencies=[Depends(require_permission("device:read"))],
)
async def test_device_authentication(
    request: AuthenticationTestRequest,
    current_user: User = Depends(get_current_active_user),
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


@router.post(
    "/test/batch",
    response_model=BaseResponse[BatchAuthenticationTestResult],
    summary="批量测试设备认证",
    dependencies=[Depends(require_permission("device:read"))],
)
async def batch_test_device_authentication(
    request: BatchAuthenticationTestRequest,
    current_user: User = Depends(get_current_active_user),
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


@router.post(
    "/username/generate",
    response_model=BaseResponse[UsernameGenerationResult],
    summary="生成动态用户名",
    dependencies=[Depends(require_permission("authentication:access"))],
)
async def generate_dynamic_username(
    request: UsernameGenerationRequest,
    current_user: User = Depends(get_current_active_user),
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


@router.post(
    "/cache/clear",
    response_model=SuccessResponse,
    summary="清除动态密码缓存",
    dependencies=[Depends(require_permission("authentication:manage"))],
)
async def clear_dynamic_password_cache(
    request: DynamicPasswordClearRequest,
    current_user: User = Depends(get_current_active_user),
):
    """清除动态密码缓存

    可以清除指定设备的动态密码缓存，或清除所有缓存。
    """
    logger.info(f"用户 {current_user.username} 请求清除动态密码缓存: device_id={request.device_id}")

    auth_manager = AuthenticationManager()
    auth_manager.clear_dynamic_password_cache(request.device_id)

    if request.device_id:
        message = f"已清除设备 {request.device_id} 的动态密码缓存"
    else:
        message = "已清除所有动态密码缓存"

    return SuccessResponse(message=message)


@router.get(
    "/cache/info",
    response_model=BaseResponse[DynamicPasswordCacheInfo],
    summary="获取动态密码缓存信息",
    dependencies=[Depends(require_permission("authentication:read"))],
)
async def get_dynamic_password_cache_info(
    current_user: User = Depends(get_current_active_user),
):
    """获取动态密码缓存信息

    返回当前缓存的动态密码数量等信息。
    """
    logger.debug(f"用户 {current_user.username} 请求获取动态密码缓存信息")

    auth_manager = AuthenticationManager()
    cached_count = auth_manager.get_cached_password_count()

    cache_info = DynamicPasswordCacheInfo(
        cached_count=cached_count,
        message=f"当前缓存了 {cached_count} 个动态密码"
    )

    return BaseResponse(
        data=cache_info,
        message="获取缓存信息成功",
    )


@router.get(
    "/config",
    response_model=BaseResponse[AuthenticationConfigInfo],
    summary="获取认证配置信息",
    dependencies=[Depends(require_permission("authentication:read"))],
)
async def get_authentication_config(
    current_user: User = Depends(get_current_active_user),
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
