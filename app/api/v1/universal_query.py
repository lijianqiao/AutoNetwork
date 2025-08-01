"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: universal_query.py
@DateTime: 2025/01/29
@Docs: 通用查询API - 基于模板的查询接口，整合了原网络查询功能
"""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.v1.permissions import Permissions
from app.core.exceptions import BusinessException
from app.core.permissions.simple_decorators import OperationContext, require_permission
from app.schemas.base import BaseResponse
from app.schemas.network_query import (
    CustomCommandQueryRequest,
    CustomCommandResult,
    InterfaceStatusQueryRequest,
    InterfaceStatusResult,
    MacQueryRequest,
    MacQueryResult,
    NetworkQueryByIPRequest,
    NetworkQueryRequest,
    NetworkQueryResponse,
    NetworkQueryTemplateListRequest,
    NetworkQueryTemplateListResponse,
)
from app.schemas.universal_query import (
    TemplateCommandsPreviewRequest,
    TemplateParametersValidationRequest,
    TemplateQueryRequest,
    TemplateTypeQueryRequest,
)
from app.services.network_query import NetworkQueryService
from app.services.universal_query import UniversalQueryService
from app.utils.deps import get_network_query_service

router = APIRouter(prefix="/universal-query", tags=["通用查询"])

# 服务实例
universal_query_service = UniversalQueryService()


@router.post("/template", summary="执行基于模板的查询", response_model=BaseResponse[dict[str, Any]])
async def execute_template_query(
    request: TemplateQueryRequest,
    operation_context: OperationContext = Depends(require_permission(Permissions.NETWORK_QUERY_EXECUTE)),
) -> BaseResponse[dict[str, Any]]:
    """
    执行基于模板的查询

    **权限要求**: `network:query:execute` - 网络查询执行权限

    **功能特性**:
    - 基于查询模板执行多设备并发查询
    - 支持查询参数模板填充
    - 支持模板版本控制
    - 支持结果解析开关
    - 自动记录查询历史

    **适用场景**:
    - 需要使用特定查询模板的场景
    - 需要精确控制查询参数的场景
    - 需要版本控制的查询场景
    """
    result = await universal_query_service.execute_template_query(request, operation_context)
    return BaseResponse(data=result)


@router.post("/template-type", summary="执行基于模板类型的查询", response_model=BaseResponse[dict[str, Any]])
async def execute_template_type_query(
    request: TemplateTypeQueryRequest,
    operation_context: OperationContext = Depends(require_permission(Permissions.NETWORK_QUERY_EXECUTE)),
) -> BaseResponse[dict[str, Any]]:
    """
    执行基于模板类型的查询

    **权限要求**: `network:query:execute` - 网络查询执行权限

    **功能特性**:
    - 自动获取指定类型下所有激活的模板
    - 并发执行多个模板的查询
    - 统一的结果格式和统计信息
    - 异常容错处理

    **适用场景**:
    - 需要执行某个类型下所有模板的场景
    - 批量查询和对比的场景
    - 探索性查询场景
    """
    result = await universal_query_service.execute_template_type_query(request, operation_context)
    return BaseResponse(data=result)


@router.post(
    "/template/{template_id}/commands/preview", summary="预览模板命令", response_model=BaseResponse[dict[str, Any]]
)
async def get_template_commands_preview(
    template_id: UUID,
    request: TemplateCommandsPreviewRequest,
    operation_context: OperationContext = Depends(require_permission(Permissions.QUERY_TEMPLATE_READ)),
) -> BaseResponse[dict[str, Any]]:
    """
    预览模板命令（不执行，仅显示命令内容）

    **权限要求**: `template:read` - 模板读取权限

    **功能特性**:
    - 展示模板下所有厂商的命令配置
    - 支持查询参数预填充预览
    - 显示命令参数缺失情况
    - 显示解析器配置信息

    **适用场景**:
    - 执行查询前的命令预览
    - 模板命令调试和验证
    - 查询参数准备
    """
    # 更新请求中的template_id以确保一致性
    request.template_id = template_id
    result = await universal_query_service.get_template_commands_preview(request, operation_context)
    return BaseResponse(data=result)


@router.post(
    "/template/{template_id}/parameters/validate", summary="验证模板参数", response_model=BaseResponse[dict[str, Any]]
)
async def validate_template_parameters(
    template_id: UUID,
    request: TemplateParametersValidationRequest,
    operation_context: OperationContext = Depends(require_permission(Permissions.QUERY_TEMPLATE_READ)),
) -> BaseResponse[dict[str, Any]]:
    """
    验证模板参数完整性

    **权限要求**: `template:read` - 模板读取权限

    **功能特性**:
    - 分析模板命令中的所有参数要求
    - 验证提供的参数是否完整
    - 按厂商分别验证参数
    - 识别缺失和多余的参数

    **适用场景**:
    - 查询执行前的参数验证
    - 模板参数调试
    - API集成时的参数检查
    """
    # 更新请求中的template_id以确保一致性
    request.template_id = template_id
    result = await universal_query_service.validate_template_parameters(request, operation_context)
    return BaseResponse(data=result)


# ===== 便捷查询接口 =====


@router.post("/mac", summary="MAC地址查询（便捷接口）", response_model=BaseResponse[dict[str, Any]])
async def execute_mac_query(
    device_ids: list[UUID],
    mac_address: str,
    operation_context: OperationContext = Depends(require_permission(Permissions.NETWORK_QUERY_MAC)),
) -> BaseResponse[dict[str, Any]]:
    """
    MAC地址查询（便捷接口）

    **权限要求**: `query:mac` - MAC查询权限

    **功能特性**:
    - 自动使用mac_query类型的所有模板
    - 预配置MAC地址查询参数
    - 统一的MAC查询结果格式
    - 支持多厂商设备

    **适用场景**:
    - 快速MAC地址定位
    - 网络故障排查
    - 终端位置查询
    """
    result = await universal_query_service.execute_mac_query(device_ids, mac_address, operation_context)
    return BaseResponse(data=result)


@router.post("/interface-status", summary="接口状态查询（便捷接口）", response_model=BaseResponse[dict[str, Any]])
async def execute_interface_status_query(
    device_ids: list[UUID],
    interface_pattern: str | None = None,
    operation_context: OperationContext = Depends(require_permission(Permissions.NETWORK_QUERY_INTERFACE)),
) -> BaseResponse[dict[str, Any]]:
    """
    接口状态查询（便捷接口）

    **权限要求**: `query:interface` - 接口查询权限

    **功能特性**:
    - 自动使用interface_status类型的所有模板
    - 支持接口模式匹配（可选）
    - 统一的接口状态结果格式
    - 支持多厂商设备

    **适用场景**:
    - 接口状态批量检查
    - 网络连通性验证
    - 接口利用率分析
    """
    result = await universal_query_service.execute_interface_status_query(
        device_ids, operation_context, interface_pattern
    )
    return BaseResponse(data=result)


@router.post("/config", summary="配置显示查询（便捷接口）", response_model=BaseResponse[dict[str, Any]])
async def execute_config_show_query(
    device_ids: list[UUID],
    config_section: str | None = None,
    operation_context: OperationContext = Depends(require_permission(Permissions.NETWORK_QUERY_CUSTOM)),
) -> BaseResponse[dict[str, Any]]:
    """
    配置显示查询（便捷接口）

    **权限要求**: `query:config` - 配置查询权限

    **功能特性**:
    - 自动使用config_show类型的所有模板
    - 支持配置节过滤（可选）
    - 统一的配置查询结果格式
    - 支持多厂商设备

    **适用场景**:
    - 设备配置检查
    - 配置合规性验证
    - 配置备份和对比
    """
    result = await universal_query_service.execute_config_show_query(device_ids, operation_context, config_section)
    return BaseResponse(data=result)


# ===== 从network_query.py迁移的功能 =====


@router.post(
    "/legacy/execute",
    response_model=BaseResponse[NetworkQueryResponse],
    summary="执行网络查询（原network_query接口）",
    description="根据设备ID执行网络查询",
)
async def execute_network_query(
    request: NetworkQueryRequest,
    service: NetworkQueryService = Depends(get_network_query_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.NETWORK_QUERY_EXECUTE)),
) -> BaseResponse[NetworkQueryResponse]:
    """执行网络查询（原network_query接口）"""
    try:
        result = await service.execute_query(request, operation_context)
        return BaseResponse(data=result)
    except BusinessException as e:
        raise BusinessException(detail=str(e)) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"网络查询执行失败: {str(e)}",
        ) from e


@router.post(
    "/legacy/execute-by-ip",
    response_model=NetworkQueryResponse,
    summary="根据IP执行网络查询（原network_query接口）",
    description="根据设备IP地址执行网络查询",
)
async def execute_network_query_by_ip(
    request: NetworkQueryByIPRequest,
    service: NetworkQueryService = Depends(get_network_query_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.NETWORK_QUERY_EXECUTE)),
) -> BaseResponse[NetworkQueryResponse]:
    """根据IP执行网络查询（原network_query接口）"""
    try:
        result = await service.execute_query_by_ip(request, operation_context)
        return BaseResponse(data=result)
    except BusinessException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"网络查询执行失败: {str(e)}",
        ) from e


@router.post(
    "/legacy/mac-query",
    response_model=BaseResponse[list[MacQueryResult]],
    summary="MAC地址查询（原network_query接口，已废弃）",
    description="在指定设备上查询MAC地址信息。建议使用 /mac 接口",
    deprecated=True,
)
async def query_mac_address_legacy(
    request: MacQueryRequest,
    service: NetworkQueryService = Depends(get_network_query_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.NETWORK_QUERY_MAC)),
) -> BaseResponse[list[MacQueryResult]]:
    """MAC地址查询（原network_query接口，已废弃）"""
    try:
        results = await service.query_mac_address(request, operation_context)
        return BaseResponse(data=results)
    except BusinessException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"MAC地址查询失败: {str(e)}",
        ) from e


@router.post(
    "/legacy/interface-status",
    response_model=BaseResponse[list[InterfaceStatusResult]],
    summary="接口状态查询（原network_query接口，已废弃）",
    description="查询指定设备的接口状态信息。建议使用 /interface-status 接口",
    deprecated=True,
)
async def query_interface_status_legacy(
    request: InterfaceStatusQueryRequest,
    service: NetworkQueryService = Depends(get_network_query_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.NETWORK_QUERY_INTERFACE)),
) -> BaseResponse[list[InterfaceStatusResult]]:
    """接口状态查询（原network_query接口，已废弃）"""
    try:
        results = await service.query_interface_status(request, operation_context)
        return BaseResponse(data=results)
    except BusinessException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"接口状态查询失败: {str(e)}",
        ) from e


@router.post(
    "/legacy/custom-commands",
    response_model=BaseResponse[list[CustomCommandResult]],
    summary="执行自定义命令（原network_query接口）",
    description="在指定设备上执行自定义命令",
)
async def execute_custom_commands_legacy(
    request: CustomCommandQueryRequest,
    service: NetworkQueryService = Depends(get_network_query_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.NETWORK_QUERY_CUSTOM)),
) -> BaseResponse[list[CustomCommandResult]]:
    """执行自定义命令（原network_query接口）"""
    try:
        results = await service.execute_custom_commands(request, operation_context)
        return BaseResponse(data=results)
    except BusinessException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"自定义命令执行失败: {str(e)}",
        ) from e


@router.get(
    "/legacy/templates",
    response_model=BaseResponse[NetworkQueryTemplateListResponse],
    summary="获取可用查询模板（原network_query接口）",
    description="获取当前用户可用的网络查询模板列表",
)
async def get_available_templates_legacy(
    template_type: str | None = None,
    service: NetworkQueryService = Depends(get_network_query_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.NETWORK_QUERY_TEMPLATE_LIST)),
) -> BaseResponse[NetworkQueryTemplateListResponse]:
    """获取可用查询模板（原network_query接口）"""
    try:
        request = NetworkQueryTemplateListRequest(template_type=template_type)
        result = await service.get_available_templates(request, operation_context)
        return BaseResponse(data=result)
    except BusinessException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取查询模板失败: {str(e)}",
        ) from e
