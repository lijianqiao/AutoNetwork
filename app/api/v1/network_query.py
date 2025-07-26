from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse

from app.core.exceptions import BusinessException
from app.core.permissions.simple_decorators import Permissions, require_permission
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
from app.services.network_query import NetworkQueryService
from app.utils.deps import (
    OperationContext,
    get_network_query_service,
)

router = APIRouter(prefix="/network-query", tags=["网络查询"])


@router.post(
    "/execute",
    response_model=NetworkQueryResponse,
    summary="执行网络查询",
    description="根据设备ID执行网络查询",
)
async def execute_network_query(
    request: NetworkQueryRequest,
    service: NetworkQueryService = Depends(get_network_query_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.NETWORK_QUERY_EXECUTE)),
) -> NetworkQueryResponse:
    """执行网络查询"""
    try:
        result = await service.execute_query(request, operation_context)
        return result
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
    "/execute-by-ip",
    response_model=NetworkQueryResponse,
    summary="根据IP执行网络查询",
    description="根据设备IP地址执行网络查询",
)
async def execute_network_query_by_ip(
    request: NetworkQueryByIPRequest,
    service: NetworkQueryService = Depends(get_network_query_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.NETWORK_QUERY_EXECUTE)),
) -> NetworkQueryResponse:
    """根据IP执行网络查询"""
    try:
        result = await service.execute_query_by_ip(request, operation_context)
        return result
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
    "/mac-query",
    response_model=list[MacQueryResult],
    summary="MAC地址查询",
    description="在指定设备上查询MAC地址信息",
)
async def query_mac_address(
    request: MacQueryRequest,
    service: NetworkQueryService = Depends(get_network_query_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.NETWORK_QUERY_MAC)),
) -> list[MacQueryResult]:
    """MAC地址查询"""
    try:
        results = await service.query_mac_address(request, operation_context)
        return results
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
    "/interface-status",
    response_model=list[InterfaceStatusResult],
    summary="接口状态查询",
    description="查询指定设备的接口状态信息",
)
async def query_interface_status(
    request: InterfaceStatusQueryRequest,
    service: NetworkQueryService = Depends(get_network_query_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.NETWORK_QUERY_INTERFACE)),
) -> list[InterfaceStatusResult]:
    """接口状态查询"""
    try:
        results = await service.query_interface_status(request, operation_context)
        return results
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
    "/custom-commands",
    response_model=list[CustomCommandResult],
    summary="执行自定义命令",
    description="在指定设备上执行自定义命令",
)
async def execute_custom_commands(
    request: CustomCommandQueryRequest,
    service: NetworkQueryService = Depends(get_network_query_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.NETWORK_QUERY_CUSTOM)),
) -> list[CustomCommandResult]:
    """执行自定义命令"""
    try:
        results = await service.execute_custom_commands(request, operation_context)
        return results
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
    "/templates",
    response_model=NetworkQueryTemplateListResponse,
    summary="获取可用查询模板",
    description="获取当前用户可用的网络查询模板列表",
)
async def get_available_templates(
    template_type: str | None = None,
    service: NetworkQueryService = Depends(get_network_query_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.NETWORK_QUERY_TEMPLATE_LIST)),
) -> NetworkQueryTemplateListResponse:
    """获取可用查询模板"""
    try:
        request = NetworkQueryTemplateListRequest(template_type=template_type)
        result = await service.get_available_templates(request, operation_context)
        return result
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


@router.get(
    "/health",
    summary="网络查询服务健康检查",
    description="检查网络查询服务的健康状态",
)
async def health_check(
    network_query_service: NetworkQueryService = Depends(get_network_query_service),
) -> JSONResponse:
    """网络查询服务健康检查"""
    try:
        # 简单的健康检查，可以扩展为更复杂的检查
        return JSONResponse(
            content={
                "status": "healthy",
                "service": "network_query",
                "message": "网络查询服务运行正常",
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "service": "network_query",
                "message": f"网络查询服务异常: {str(e)}",
            },
        )
