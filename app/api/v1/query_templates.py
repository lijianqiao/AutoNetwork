"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: query_templates.py
@DateTime: 2025/07/23
@Docs: 查询模板管理API端点
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.permissions.simple_decorators import (
    Permissions,
    require_permission,
)
from app.schemas.base import SuccessResponse
from app.schemas.query_template import (
    QueryTemplateCreateRequest,
    QueryTemplateDetailResponse,
    QueryTemplateListRequest,
    QueryTemplateListResponse,
    QueryTemplateResponse,
    QueryTemplateUpdateRequest,
)
from app.services.query_template import QueryTemplateService
from app.utils.deps import OperationContext, get_query_template_service

router = APIRouter(prefix="/query-templates", tags=["查询模板管理"])


@router.get("", response_model=QueryTemplateListResponse, summary="获取查询模板列表")
async def list_query_templates(
    query: QueryTemplateListRequest = Depends(),
    service: QueryTemplateService = Depends(get_query_template_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.QUERY_TEMPLATE_READ)),
):
    """获取查询模板列表（分页），支持搜索和筛选"""
    templates, total = await service.get_templates(query, operation_context=operation_context)
    return QueryTemplateListResponse(data=templates, total=total, page=query.page, page_size=query.page_size)


@router.get("/{template_id}", response_model=QueryTemplateDetailResponse, summary="获取查询模板详情")
async def get_query_template(
    template_id: UUID,
    service: QueryTemplateService = Depends(get_query_template_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.QUERY_TEMPLATE_READ)),
):
    """获取查询模板详情"""
    template = await service.get_template_detail(template_id, operation_context=operation_context)
    if template:
        return template
    raise HTTPException(status_code=404, detail="查询模板不存在")


@router.post("", response_model=QueryTemplateResponse, status_code=status.HTTP_201_CREATED, summary="创建查询模板")
async def create_query_template(
    template_data: QueryTemplateCreateRequest,
    service: QueryTemplateService = Depends(get_query_template_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.QUERY_TEMPLATE_CREATE)),
):
    """创建新查询模板"""
    return await service.create(operation_context, **template_data.model_dump())


@router.put("/{template_id}", response_model=QueryTemplateResponse, summary="更新查询模板")
async def update_query_template(
    template_id: UUID,
    template_data: QueryTemplateUpdateRequest,
    service: QueryTemplateService = Depends(get_query_template_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.QUERY_TEMPLATE_UPDATE)),
):
    """更新查询模板信息"""
    return await service.update(template_id, operation_context, **template_data.model_dump(exclude_none=True))


@router.delete("/{template_id}", response_model=SuccessResponse, summary="删除查询模板")
async def delete_query_template(
    template_id: UUID,
    service: QueryTemplateService = Depends(get_query_template_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.QUERY_TEMPLATE_DELETE)),
):
    """删除查询模板"""
    await service.delete(template_id, operation_context)
    return SuccessResponse(message="查询模板删除成功")


# ===== 批量操作功能 =====


@router.post("/batch", response_model=list[QueryTemplateResponse], summary="批量创建查询模板")
async def batch_create_query_templates(
    templates_data: list[QueryTemplateCreateRequest],
    service: QueryTemplateService = Depends(get_query_template_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.QUERY_TEMPLATE_CREATE)),
):
    """批量创建查询模板"""
    results = []
    for template_data in templates_data:
        result = await service.create(operation_context, **template_data.model_dump())
        results.append(result)
    return results


@router.put("/batch", response_model=list[QueryTemplateResponse], summary="批量更新查询模板")
async def batch_update_query_templates(
    updates_data: list[dict],  # [{"id": UUID, "data": QueryTemplateUpdateRequest}]
    service: QueryTemplateService = Depends(get_query_template_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.QUERY_TEMPLATE_UPDATE)),
):
    """批量更新查询模板"""
    results = []
    for update_item in updates_data:
        template_id = update_item["id"]
        template_data = QueryTemplateUpdateRequest(**update_item["data"])
        result = await service.update(template_id, operation_context, **template_data.model_dump(exclude_none=True))
        results.append(result)
    return results


@router.delete("/batch", response_model=SuccessResponse, summary="批量删除查询模板")
async def batch_delete_query_templates(
    template_ids: list[UUID],
    service: QueryTemplateService = Depends(get_query_template_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.QUERY_TEMPLATE_DELETE)),
):
    """批量删除查询模板"""
    for template_id in template_ids:
        await service.delete(template_id, operation_context)
    return SuccessResponse(message=f"成功删除 {len(template_ids)} 个查询模板")
