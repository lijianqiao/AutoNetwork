"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: vendors.py
@DateTime: 2025/07/23
@Docs: 厂商管理API端点
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.permissions.simple_decorators import (
    Permissions,
    require_permission,
)
from app.schemas.base import SuccessResponse
from app.schemas.vendor import (
    VendorCreateRequest,
    VendorDetailResponse,
    VendorListRequest,
    VendorListResponse,
    VendorResponse,
    VendorUpdateRequest,
)
from app.services.vendor import VendorService
from app.utils.deps import OperationContext, get_vendor_service

router = APIRouter(prefix="/vendors", tags=["厂商管理"])


@router.get("", response_model=VendorListResponse, summary="获取厂商列表")
async def list_vendors(
    query: VendorListRequest = Depends(),
    service: VendorService = Depends(get_vendor_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.VENDOR_READ)),
):
    """获取厂商列表（分页），支持搜索和筛选"""
    vendors, total = await service.get_vendors(query, operation_context=operation_context)
    return VendorListResponse(data=vendors, total=total, page=query.page, page_size=query.page_size)


@router.get("/{vendor_id}", response_model=VendorDetailResponse, summary="获取厂商详情")
async def get_vendor(
    vendor_id: UUID,
    service: VendorService = Depends(get_vendor_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.VENDOR_READ)),
):
    """获取厂商详情"""
    vendor = await service.get_vendor_detail(vendor_id, operation_context=operation_context)
    if not vendor:
        raise HTTPException(status_code=404, detail="厂商不存在")
    return vendor


@router.post("", response_model=VendorResponse, status_code=status.HTTP_201_CREATED, summary="创建厂商")
async def create_vendor(
    vendor_data: VendorCreateRequest,
    service: VendorService = Depends(get_vendor_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.VENDOR_CREATE)),
):
    """创建新厂商"""
    return await service.create_vendor(vendor_data, operation_context=operation_context)


@router.put("/{vendor_id}", response_model=VendorResponse, summary="更新厂商")
async def update_vendor(
    vendor_id: UUID,
    vendor_data: VendorUpdateRequest,
    service: VendorService = Depends(get_vendor_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.VENDOR_UPDATE)),
):
    """更新厂商信息"""
    return await service.update_vendor(vendor_id, vendor_data, operation_context=operation_context)


@router.delete("/{vendor_id}", response_model=SuccessResponse, summary="删除厂商")
async def delete_vendor(
    vendor_id: UUID,
    service: VendorService = Depends(get_vendor_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.VENDOR_DELETE)),
):
    """删除厂商"""
    await service.delete_vendor(vendor_id, operation_context=operation_context)
    return SuccessResponse(message="厂商删除成功")


# ===== 批量操作功能 =====


@router.post("/batch", response_model=list[VendorResponse], summary="批量创建厂商")
async def batch_create_vendors(
    vendors_data: list[VendorCreateRequest],
    service: VendorService = Depends(get_vendor_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.VENDOR_CREATE)),
):
    """批量创建厂商"""
    return await service.batch_create_vendors(vendors_data, operation_context)


@router.put("/batch", response_model=list[VendorResponse], summary="批量更新厂商")
async def batch_update_vendors(
    updates_data: list[dict],  # [{"id": UUID, "data": VendorUpdateRequest}]
    service: VendorService = Depends(get_vendor_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.VENDOR_UPDATE)),
):
    """批量更新厂商"""
    return await service.batch_update_vendors(updates_data, operation_context)


@router.delete("/batch", response_model=SuccessResponse, summary="批量删除厂商")
async def batch_delete_vendors(
    vendor_ids: list[UUID],
    service: VendorService = Depends(get_vendor_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.VENDOR_DELETE)),
):
    """批量删除厂商"""
    deleted_count = await service.batch_delete_vendors(vendor_ids, operation_context)
    return SuccessResponse(message=f"成功删除 {deleted_count} 个厂商")


@router.get("/code/{vendor_code}", response_model=VendorDetailResponse, summary="根据代码获取厂商")
async def get_vendor_by_code(
    vendor_code: str,
    service: VendorService = Depends(get_vendor_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.VENDOR_READ)),
):
    """根据厂商代码获取厂商信息"""
    vendor = await service.get_vendor_by_code(vendor_code, operation_context=operation_context)
    if not vendor:
        raise HTTPException(status_code=404, detail="厂商不存在")
    return vendor
