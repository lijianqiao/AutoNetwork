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
from app.schemas.base import BaseResponse, SuccessResponse
from app.schemas.query_template import (
    QueryTemplateActivateRequest,
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


@router.get("", response_model=BaseResponse[QueryTemplateListResponse], summary="获取查询模板列表")
async def list_query_templates(
    query: QueryTemplateListRequest = Depends(),
    service: QueryTemplateService = Depends(get_query_template_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.QUERY_TEMPLATE_READ)),
):
    """获取查询模板列表（分页），支持搜索和筛选"""
    templates, total = await service.get_templates(query, operation_context=operation_context)
    response = QueryTemplateListResponse(
        data=[QueryTemplateResponse.model_validate(template) for template in templates],
        total=total,
        page=query.page,
        page_size=query.page_size,
    )
    return BaseResponse(data=response)


@router.get("/{template_id}", response_model=BaseResponse[QueryTemplateDetailResponse], summary="获取查询模板详情")
async def get_query_template(
    template_id: UUID,
    service: QueryTemplateService = Depends(get_query_template_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.QUERY_TEMPLATE_READ)),
):
    """获取查询模板详情"""
    template = await service.get_template_detail(template_id, operation_context=operation_context)
    if template:
        return BaseResponse(data=template)
    raise HTTPException(status_code=404, detail="查询模板不存在")


@router.post(
    "", response_model=BaseResponse[QueryTemplateResponse], status_code=status.HTTP_201_CREATED, summary="创建查询模板"
)
async def create_query_template(
    template_data: QueryTemplateCreateRequest,
    service: QueryTemplateService = Depends(get_query_template_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.QUERY_TEMPLATE_CREATE)),
):
    """创建新查询模板"""
    result = await service.create(operation_context, **template_data.model_dump())
    return BaseResponse(data=result)


@router.put("/{template_id}", response_model=BaseResponse[QueryTemplateResponse], summary="更新查询模板")
async def update_query_template(
    template_id: UUID,
    template_data: QueryTemplateUpdateRequest,
    service: QueryTemplateService = Depends(get_query_template_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.QUERY_TEMPLATE_UPDATE)),
):
    """更新查询模板信息"""
    result = await service.update(template_id, operation_context, **template_data.model_dump(exclude_none=True))
    return BaseResponse(data=result)


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


@router.post("/batch", response_model=BaseResponse[list[QueryTemplateResponse]], summary="批量创建查询模板")
async def batch_create_query_templates(
    templates_data: list[QueryTemplateCreateRequest],
    service: QueryTemplateService = Depends(get_query_template_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.QUERY_TEMPLATE_CREATE)),
):
    """批量创建查询模板"""
    result = await service.batch_create_templates(templates_data, operation_context)
    return BaseResponse(data=result)


@router.put("/batch", response_model=BaseResponse[list[QueryTemplateResponse]], summary="批量更新查询模板")
async def batch_update_query_templates(
    updates_data: list[dict],  # [{"id": UUID, "data": QueryTemplateUpdateRequest}]
    service: QueryTemplateService = Depends(get_query_template_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.QUERY_TEMPLATE_UPDATE)),
):
    """批量更新查询模板"""
    # 将数据格式转换为服务层期望的格式
    formatted_updates = []
    for update_item in updates_data:
        template_id = update_item["id"]
        template_data = update_item["data"]
        formatted_update = {"id": template_id, **template_data}
        formatted_updates.append(formatted_update)

    result = await service.batch_update_templates(formatted_updates, operation_context)
    return BaseResponse(data=result)


@router.delete("/batch", response_model=SuccessResponse, summary="批量删除查询模板")
async def batch_delete_query_templates(
    template_ids: list[UUID],
    service: QueryTemplateService = Depends(get_query_template_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.QUERY_TEMPLATE_DELETE)),
):
    """批量删除查询模板"""
    deleted_count = await service.batch_delete_templates(template_ids, operation_context)
    return SuccessResponse(message=f"成功删除 {deleted_count} 个查询模板")


# ===== 激活/禁用功能 =====


@router.put("/{template_id}/activate", response_model=BaseResponse[QueryTemplateResponse], summary="激活查询模板")
async def activate_query_template(
    template_id: UUID,
    service: QueryTemplateService = Depends(get_query_template_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.QUERY_TEMPLATE_ACTIVATE)),
):
    """激活查询模板"""
    result = await service.activate_template(template_id, operation_context)
    return BaseResponse(data=result)


@router.put("/{template_id}/deactivate", response_model=BaseResponse[QueryTemplateResponse], summary="停用查询模板")
async def deactivate_query_template(
    template_id: UUID,
    service: QueryTemplateService = Depends(get_query_template_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.QUERY_TEMPLATE_ACTIVATE)),
):
    """停用查询模板"""
    result = await service.deactivate_template(template_id, operation_context)
    return BaseResponse(data=result)


@router.put("/batch/activate", response_model=BaseResponse[dict], summary="批量激活/停用查询模板")
async def batch_activate_query_templates(
    request_data: QueryTemplateActivateRequest,
    service: QueryTemplateService = Depends(get_query_template_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.QUERY_TEMPLATE_ACTIVATE)),
):
    """批量激活/停用查询模板"""
    result = await service.batch_activate_templates(request_data, operation_context)
    return BaseResponse(data=result)


# ===== 查询功能 =====


@router.get("/active", response_model=BaseResponse[list[QueryTemplateResponse]], summary="获取所有激活的查询模板")
async def get_active_query_templates(
    service: QueryTemplateService = Depends(get_query_template_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.QUERY_TEMPLATE_READ)),
):
    """获取所有激活的查询模板"""
    result = await service.get_active_templates(operation_context)
    return BaseResponse(data=result)


@router.get(
    "/type/{template_type}", response_model=BaseResponse[list[QueryTemplateResponse]], summary="根据类型获取查询模板"
)
async def get_query_templates_by_type(
    template_type: str,
    service: QueryTemplateService = Depends(get_query_template_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.QUERY_TEMPLATE_READ)),
):
    """根据模板类型获取查询模板"""
    result = await service.get_templates_by_type(template_type, operation_context)
    return BaseResponse(data=result)


@router.get(
    "/with-commands", response_model=BaseResponse[list[QueryTemplateResponse]], summary="获取包含厂商命令的查询模板"
)
async def get_query_templates_with_commands(
    service: QueryTemplateService = Depends(get_query_template_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.QUERY_TEMPLATE_READ)),
):
    """获取包含厂商命令的查询模板"""
    result = await service.get_templates_with_commands(operation_context)
    return BaseResponse(data=result)
