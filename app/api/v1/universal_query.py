"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: universal_query.py
@DateTime: 2025/01/29
@Docs: 通用查询API - 基于模板的查询接口
"""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends

from app.api.v1.permissions import Permissions
from app.core.permissions.simple_decorators import OperationContext, require_permission
from app.schemas.base import BaseResponse
from app.schemas.universal_query import (
    TemplateCommandsPreviewRequest,
    TemplateParametersValidationRequest,
    TemplateQueryRequest,
    TemplateTypeQueryRequest,
)
from app.services.universal_query import UniversalQueryService

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


@router.get("/stats", summary="获取查询引擎统计信息", response_model=BaseResponse[dict[str, Any]])
async def get_query_engine_stats(
    operation_context: OperationContext = Depends(require_permission(Permissions.NETWORK_QUERY_ACCESS)),
) -> BaseResponse[dict[str, Any]]:
    """
    获取查询引擎统计信息

    **权限要求**: `system:monitor` - 系统监控权限

    **功能特性**:
    - 通用查询引擎状态信息
    - 模板统计信息
    - 底层Nornir引擎统计
    - 并发控制状态

    **适用场景**:
    - 系统监控和运维
    - 性能分析和优化
    - 问题诊断和排查
    """
    result = await universal_query_service.get_query_engine_stats(operation_context)
    return BaseResponse(data=result)


@router.get("/health", summary="查询引擎健康检查", response_model=BaseResponse[dict[str, Any]])
async def get_query_engine_health(
    operation_context: OperationContext = Depends(require_permission(Permissions.NETWORK_QUERY_ACCESS)),
) -> BaseResponse[dict[str, Any]]:
    """
    查询引擎健康检查

    **权限要求**: `system:monitor` - 系统监控权限

    **功能特性**:
    - 整体健康状态评估
    - 各组件健康状态检查
    - 数据库连接状态验证
    - 底层引擎健康状态

    **适用场景**:
    - 系统健康监控
    - 负载均衡健康检查
    - 自动化运维检查
    """
    result = await universal_query_service.get_query_engine_health(operation_context)
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
