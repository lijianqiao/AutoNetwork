"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: regions.py
@DateTime: 2025/07/23
@Docs: 基地管理API端点
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.permissions.simple_decorators import (
    Permissions,
    require_permission,
)
from app.schemas.base import SuccessResponse
from app.schemas.region import (
    RegionCreateRequest,
    RegionDetailResponse,
    RegionListRequest,
    RegionListResponse,
    RegionResponse,
    RegionUpdateRequest,
)
from app.services.region import RegionService
from app.utils.deps import OperationContext, get_region_service

router = APIRouter(prefix="/regions", tags=["基地管理"])


@router.get("", response_model=RegionListResponse, summary="获取基地列表")
async def list_regions(
    query: RegionListRequest = Depends(),
    service: RegionService = Depends(get_region_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.REGION_READ)),
):
    """获取基地列表（分页），支持搜索和筛选"""
    regions, total = await service.get_regions(query, operation_context=operation_context)
    return RegionListResponse(data=regions, total=total, page=query.page, page_size=query.page_size)


@router.get("/{region_id}", response_model=RegionDetailResponse, summary="获取基地详情")
async def get_region(
    region_id: UUID,
    service: RegionService = Depends(get_region_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.REGION_READ)),
):
    """获取基地详情"""
    region = await service.get_region_detail(region_id, operation_context=operation_context)
    if not region:
        raise HTTPException(status_code=404, detail="基地不存在")
    return region


@router.post("", response_model=RegionResponse, status_code=status.HTTP_201_CREATED, summary="创建基地")
async def create_region(
    region_data: RegionCreateRequest,
    service: RegionService = Depends(get_region_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.REGION_CREATE)),
):
    """创建新基地"""
    return await service.create_region(region_data, operation_context=operation_context)


@router.put("/{region_id}", response_model=RegionResponse, summary="更新基地")
async def update_region(
    region_id: UUID,
    region_data: RegionUpdateRequest,
    service: RegionService = Depends(get_region_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.REGION_UPDATE)),
):
    """更新基地信息"""
    return await service.update_region(region_id, region_data, operation_context=operation_context)


@router.delete("/{region_id}", response_model=SuccessResponse, summary="删除基地")
async def delete_region(
    region_id: UUID,
    service: RegionService = Depends(get_region_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.REGION_DELETE)),
):
    """删除基地"""
    await service.delete_region(region_id, operation_context=operation_context)
    return SuccessResponse(message="基地删除成功")


# ===== 批量操作功能 =====


@router.post("/batch", response_model=list[RegionResponse], summary="批量创建基地")
async def batch_create_regions(
    regions_data: list[RegionCreateRequest],
    service: RegionService = Depends(get_region_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.REGION_CREATE)),
):
    """批量创建基地"""
    results = []
    for region_data in regions_data:
        result = await service.create_region(region_data, operation_context=operation_context)
        results.append(result)
    return results


@router.put("/batch", response_model=list[RegionResponse], summary="批量更新基地")
async def batch_update_regions(
    updates_data: list[dict],  # [{"id": UUID, "data": RegionUpdateRequest}]
    service: RegionService = Depends(get_region_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.REGION_UPDATE)),
):
    """批量更新基地"""
    results = []
    for update_item in updates_data:
        region_id = update_item["id"]
        region_data = RegionUpdateRequest(**update_item["data"])
        result = await service.update_region(region_id, region_data, operation_context=operation_context)
        results.append(result)
    return results


@router.delete("/batch", response_model=SuccessResponse, summary="批量删除基地")
async def batch_delete_regions(
    region_ids: list[UUID],
    service: RegionService = Depends(get_region_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.REGION_DELETE)),
):
    """批量删除基地"""
    for region_id in region_ids:
        await service.delete_region(region_id, operation_context=operation_context)
    return SuccessResponse(message=f"成功删除 {len(region_ids)} 个基地")


@router.get("/code/{region_code}", response_model=RegionDetailResponse, summary="根据代码获取基地")
async def get_region_by_code(
    region_code: str,
    service: RegionService = Depends(get_region_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.REGION_READ)),
):
    """根据基地代码获取基地信息"""
    region = await service.get_region_by_code(region_code, operation_context=operation_context)
    if not region:
        raise HTTPException(status_code=404, detail="基地不存在")
    return region
