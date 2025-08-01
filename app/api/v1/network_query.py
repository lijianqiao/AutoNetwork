"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: network_query.py
@DateTime: 2025/08/01
@Docs: 统一网络查询API - 提供统一的查询接口，支持所有查询类型
"""

from typing import Any

from fastapi import APIRouter, Depends

from app.api.v1.permissions import Permissions
from app.core.exceptions import BusinessException
from app.core.permissions.simple_decorators import OperationContext, require_permission
from app.schemas.base import BaseResponse
from app.schemas.unified_query import (
    CustomCommandQueryConvenienceRequest,
    InterfaceStatusQueryConvenienceRequest,
    MacQueryConvenienceRequest,
    UnifiedQueryRequest,
    UnifiedQueryResponse,
)
from app.services.network_query import NetworkQueryService

router = APIRouter(prefix="/network-query", tags=["网络查询"])

# 服务实例
network_query_service = NetworkQueryService()


@router.post("/unified", summary="统一查询接口", response_model=BaseResponse[UnifiedQueryResponse])
async def execute_unified_query(
    request: UnifiedQueryRequest,
    operation_context: OperationContext = Depends(require_permission(Permissions.NETWORK_QUERY_EXECUTE)),
) -> BaseResponse[UnifiedQueryResponse]:
    """
    统一查询接口 - 支持所有类型的网络查询

    **权限要求**: `network:query:execute` - 网络查询执行权限

    **支持的查询类型**:
    - `template`: 基于模板ID的查询
    - `template_type`: 基于模板类型的查询
    - `mac_address`: MAC地址查询
    - `interface_status`: 接口状态查询
    - `custom_command`: 自定义命令查询

    **功能特性**:
    - 统一的请求和响应格式
    - 自动查询分发和结果聚合
    - 支持并发查询和超时控制
    - 自动记录查询历史和操作日志
    - 完整的错误处理和异常报告

    **使用示例**:
    ```json
    {
        "query_type": "mac_address",
        "device_ids": ["uuid1", "uuid2"],
        "parameters": {"mac_address": "00:11:22:33:44:55"},
        "timeout": 30,
        "max_concurrent": 10
    }
    ```
    """
    try:
        result = await network_query_service.execute_unified_query(request, operation_context)
        return BaseResponse(data=result)
    except Exception as e:
        raise BusinessException(message="查询执行失败", detail=str(e)) from e


# ==================== 便捷查询接口（向后兼容）====================


@router.post("/mac", summary="MAC地址查询", response_model=BaseResponse[UnifiedQueryResponse])
async def execute_mac_query(
    request: MacQueryConvenienceRequest,
    operation_context: OperationContext = Depends(require_permission(Permissions.NETWORK_QUERY_EXECUTE)),
) -> BaseResponse[UnifiedQueryResponse]:
    """
    MAC地址查询便捷接口

    **权限要求**: `network:query:execute` - 网络查询执行权限

    **功能特性**:
    - 基于MAC地址在指定设备上查询对应的接口信息
    - 自动使用mac_query模板类型
    - 支持结果解析和格式化

    **适用场景**:
    - 网络故障排查
    - 设备接入位置定位
    - 网络拓扑分析
    """
    try:
        # 转换为统一查询请求
        unified_request = request.to_unified_request()
        result = await network_query_service.execute_unified_query(unified_request, operation_context)
        return BaseResponse(data=result)

    except Exception as e:
        raise BusinessException(message="MAC查询失败", detail=str(e)) from e


@router.post("/interface-status", summary="接口状态查询", response_model=BaseResponse[UnifiedQueryResponse])
async def execute_interface_status_query(
    request: InterfaceStatusQueryConvenienceRequest,
    operation_context: OperationContext = Depends(require_permission(Permissions.NETWORK_QUERY_EXECUTE)),
) -> BaseResponse[UnifiedQueryResponse]:
    """
    接口状态查询便捷接口

    **权限要求**: `network:query:execute` - 网络查询执行权限

    **功能特性**:
    - 查询设备所有接口的状态信息
    - 自动使用interface_status模板类型
    - 支持结果解析和状态统计

    **适用场景**:
    - 设备接口监控
    - 网络链路状态检查
    - 接口利用率分析
    """
    try:
        # 转换为统一查询请求
        unified_request = request.to_unified_request()
        result = await network_query_service.execute_unified_query(unified_request, operation_context)
        return BaseResponse(data=result)

    except Exception as e:
        raise BusinessException(message="接口状态查询失败", detail=str(e)) from e


@router.post("/custom-command", summary="自定义命令查询", response_model=BaseResponse[UnifiedQueryResponse])
async def execute_custom_command_query(
    request: CustomCommandQueryConvenienceRequest,
    operation_context: OperationContext = Depends(require_permission(Permissions.NETWORK_QUERY_EXECUTE)),
) -> BaseResponse[UnifiedQueryResponse]:
    """
    自定义命令查询便捷接口

    **权限要求**: `network:query:execute` - 网络查询执行权限

    **功能特性**:
    - 在指定设备上执行自定义命令
    - 原始命令输出返回
    - 支持超时控制和并发限制

    **适用场景**:
    - 临时故障排查
    - 特殊命令执行
    - 设备配置检查

    **注意事项**:
    - 请谨慎使用，避免执行危险命令
    - 命令执行会被完整记录在操作日志中
    - 建议优先使用模板查询代替自定义命令
    """
    try:
        # 转换为统一查询请求
        unified_request = request.to_unified_request()
        result = await network_query_service.execute_unified_query(unified_request, operation_context)
        return BaseResponse(data=result)

    except Exception as e:
        raise BusinessException(message="自定义命令执行失败", detail=str(e)) from e


# ==================== 查询支持接口 ====================


@router.get("/status", summary="查询服务状态", response_model=BaseResponse[dict[str, Any]])
async def get_query_service_status(
    operation_context: OperationContext = Depends(require_permission(Permissions.NETWORK_QUERY_EXECUTE)),
) -> BaseResponse[dict[str, Any]]:
    """
    获取查询服务状态

    **权限要求**: `network:query:execute` - 网络查询执行权限

    **功能特性**:
    - 查询服务运行状态
    - 统一查询架构信息
    """
    try:
        return BaseResponse(
            data={
                "service_status": "active",
                "unified_query_enabled": True,
                "supported_query_types": [
                    "template",
                    "template_type",
                    "mac_address",
                    "interface_status",
                    "custom_command",
                ],
                "version": "2.0.0-unified",
            }
        )
    except Exception as e:
        raise BusinessException(message="获取服务状态失败", detail=str(e)) from e
