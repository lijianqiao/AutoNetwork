"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: device_configs.py
@DateTime: 2025/07/23
@Docs: 设备配置快照管理API端点
"""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.permissions.simple_decorators import (
    Permissions,
    require_permission,
)
from app.schemas.base import SuccessResponse
from app.schemas.device_config import (
    DeviceConfigBackupRequest,
    DeviceConfigBackupResponse,
    DeviceConfigBackupResult,
    DeviceConfigCleanupRequest,
    DeviceConfigCleanupResponse,
    DeviceConfigCompareRequest,
    DeviceConfigCompareResponse,
    DeviceConfigCreateRequest,
    DeviceConfigDetailResponse,
    DeviceConfigListRequest,
    DeviceConfigListResponse,
    DeviceConfigResponse,
    DeviceConfigUpdateRequest,
)
from app.services.device_config import DeviceConfigService
from app.utils.deps import OperationContext, get_device_config_service

router = APIRouter(prefix="/device-configs", tags=["设备配置管理"])


@router.get("", response_model=DeviceConfigListResponse, summary="获取配置快照列表")
async def list_device_configs(
    query: DeviceConfigListRequest = Depends(),
    service: DeviceConfigService = Depends(get_device_config_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.DEVICE_CONFIG_READ)),
):
    """获取设备配置快照列表（分页），支持搜索和筛选"""
    configs, total = await service.get_configs_paginated(
        page=query.page,
        page_size=query.page_size,
        device_id=query.device_id,
        config_type=query.config_type,
    )
    # 转换为响应模型
    config_responses = [DeviceConfigResponse.model_validate(config) for config in configs]
    return DeviceConfigListResponse(data=config_responses, total=total, page=query.page, page_size=query.page_size)


@router.get("/{config_id}", response_model=DeviceConfigDetailResponse, summary="获取配置快照详情")
async def get_device_config(
    config_id: UUID,
    service: DeviceConfigService = Depends(get_device_config_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.DEVICE_CONFIG_READ)),
):
    """获取配置快照详情"""
    config = await service.get_config_with_details(config_id)
    if not config:
        raise HTTPException(status_code=404, detail="配置快照不存在")
    return DeviceConfigDetailResponse.model_validate(config)


@router.post("", response_model=DeviceConfigResponse, status_code=status.HTTP_201_CREATED, summary="创建配置快照")
async def create_device_config(
    config_data: DeviceConfigCreateRequest,
    service: DeviceConfigService = Depends(get_device_config_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.DEVICE_CONFIG_CREATE)),
):
    """手动创建设备配置快照"""
    config = await service.create_config_snapshot(
        device_id=config_data.device_id,
        config_type=config_data.config_type,
        config_content=config_data.config_content,
        backup_reason=config_data.backup_reason,
        operation_context=operation_context,
    )
    return DeviceConfigResponse.model_validate(config)


@router.put("/{config_id}", response_model=DeviceConfigResponse, summary="更新配置快照")
async def update_device_config(
    config_id: UUID,
    config_data: DeviceConfigUpdateRequest,
    service: DeviceConfigService = Depends(get_device_config_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.DEVICE_CONFIG_UPDATE)),
):
    """更新配置快照信息（主要是备份原因）"""
    if config_data.backup_reason is not None:
        config = await service.update_config_reason(config_id, config_data.backup_reason, operation_context)
        return DeviceConfigResponse.model_validate(config)

    raise HTTPException(status_code=400, detail="没有提供需要更新的字段")


@router.delete("/{config_id}", response_model=SuccessResponse, summary="删除配置快照")
async def delete_device_config(
    config_id: UUID,
    service: DeviceConfigService = Depends(get_device_config_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.DEVICE_CONFIG_DELETE)),
):
    """删除配置快照"""
    await service.batch_delete_configs([config_id], operation_context)
    return SuccessResponse(message="配置快照删除成功")


# ===== 配置对比功能 =====


@router.post("/compare", response_model=DeviceConfigCompareResponse, summary="对比配置快照")
async def compare_device_configs(
    compare_data: DeviceConfigCompareRequest,
    service: DeviceConfigService = Depends(get_device_config_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.DEVICE_CONFIG_COMPARE)),
):
    """对比两个配置快照的差异"""
    comparison_result = await service.compare_configs(compare_data.config1_id, compare_data.config2_id)

    # 转换为API响应格式
    differences = []
    for diff in comparison_result["differences"]:
        differences.append(
            {
                "line_number": diff["line_number"],
                "change_type": "modified",  # 简化处理，都标记为修改
                "old_content": diff["config1_line"],
                "new_content": diff["config2_line"],
            }
        )

    return DeviceConfigCompareResponse(
        config1_info=comparison_result["config1"],
        config2_info=comparison_result["config2"],
        is_identical=comparison_result["is_identical"],
        differences=differences,
        added_lines=0,  # TODO: 实现具体的增减行数统计
        removed_lines=0,
        modified_lines=len(differences),
    )


# ===== 设备相关的配置管理 =====


@router.get("/device/{device_id}/latest", response_model=DeviceConfigResponse | None, summary="获取设备最新配置")
async def get_device_latest_config(
    device_id: UUID,
    config_type: str = Query(default="running", description="配置类型"),
    service: DeviceConfigService = Depends(get_device_config_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.DEVICE_CONFIG_READ)),
):
    """获取设备的最新配置快照"""
    config = await service.get_latest_config(device_id, config_type)
    if not config:
        raise HTTPException(status_code=404, detail="未找到设备的配置快照")
    return DeviceConfigResponse.model_validate(config)


@router.get("/device/{device_id}/history", response_model=list[DeviceConfigResponse], summary="获取设备配置历史")
async def get_device_config_history(
    device_id: UUID,
    config_type: str | None = Query(default=None, description="配置类型筛选"),
    limit: int = Query(default=50, description="返回数量限制", ge=1, le=100),
    service: DeviceConfigService = Depends(get_device_config_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.DEVICE_CONFIG_READ)),
):
    """获取设备的配置历史记录"""
    configs = await service.get_device_configs(device_id, config_type, limit)
    return [DeviceConfigResponse.model_validate(config) for config in configs]


@router.get("/device/{device_id}/changes", response_model=list[DeviceConfigResponse], summary="获取设备配置变更")
async def get_device_config_changes(
    device_id: UUID,
    days: int = Query(default=30, description="查询天数", ge=1, le=365),
    service: DeviceConfigService = Depends(get_device_config_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.DEVICE_CONFIG_READ)),
):
    """获取设备指定天数内的配置变更历史"""
    configs = await service.get_config_changes(device_id, days)
    return [DeviceConfigResponse.model_validate(config) for config in configs]


# ===== 批量操作功能 =====


@router.post("/batch-backup", response_model=DeviceConfigBackupResponse, summary="批量备份设备配置")
async def batch_backup_device_configs(
    backup_data: DeviceConfigBackupRequest,
    service: DeviceConfigService = Depends(get_device_config_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.DEVICE_CONFIG_BACKUP)),
):
    """批量备份设备配置"""
    # TODO: 实现实际的设备连接和配置获取逻辑
    # 这里只是示例响应
    results = []
    success_count = 0

    for device_id in backup_data.device_ids:
        try:
            # 模拟配置备份逻辑
            config = await service.create_config_snapshot(
                device_id=device_id,
                config_type=backup_data.config_type if backup_data.config_type != "both" else "running",
                config_content="# 模拟配置内容\nhostname test-device\n",
                backup_reason=backup_data.backup_reason,
                operation_context=operation_context,
            )

            results.append(
                DeviceConfigBackupResult(
                    device_id=device_id,
                    hostname=f"device-{device_id}",
                    success=True,
                    config_ids=[config.id],
                    error_message=None,
                )
            )
            success_count += 1
        except Exception as e:
            results.append(
                DeviceConfigBackupResult(
                    device_id=device_id,
                    hostname=f"device-{device_id}",
                    success=False,
                    config_ids=[],
                    error_message=str(e),
                )
            )

    return DeviceConfigBackupResponse(
        total_count=len(backup_data.device_ids),
        success_count=success_count,
        failed_count=len(backup_data.device_ids) - success_count,
        results=results,
    )


# ===== 批量操作功能 =====


@router.post("/batch", response_model=list[DeviceConfigResponse], summary="批量创建配置快照")
async def batch_create_device_configs(
    configs_data: list[dict],  # [{"device_id": UUID, "config_type": str, "config_content": str, ...}]
    service: DeviceConfigService = Depends(get_device_config_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.DEVICE_CONFIG_CREATE)),
):
    """批量创建设备配置快照"""
    created_configs = await service.batch_create_configs(configs_data, operation_context)
    return [DeviceConfigResponse.model_validate(config) for config in created_configs]


@router.put("/batch", response_model=list[DeviceConfigResponse], summary="批量更新配置快照")
async def batch_update_device_configs(
    updates_data: list[dict],  # [{"id": UUID, **update_fields}]
    service: DeviceConfigService = Depends(get_device_config_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.DEVICE_CONFIG_UPDATE)),
):
    """批量更新设备配置快照"""
    updated_configs = await service.batch_update_configs(updates_data, operation_context)
    return [DeviceConfigResponse.model_validate(config) for config in updated_configs]


@router.delete("/batch", response_model=SuccessResponse, summary="批量删除配置快照")
async def batch_delete_device_configs(
    config_ids: list[UUID],
    service: DeviceConfigService = Depends(get_device_config_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.DEVICE_CONFIG_DELETE)),
):
    """批量删除配置快照"""
    deleted_count = await service.batch_delete_configs(config_ids, operation_context)
    return SuccessResponse(message=f"成功删除 {deleted_count} 个配置快照")


# ===== 配置清理功能 =====


@router.post("/cleanup", response_model=DeviceConfigCleanupResponse, summary="清理旧配置快照")
async def cleanup_old_configs(
    cleanup_data: DeviceConfigCleanupRequest,
    service: DeviceConfigService = Depends(get_device_config_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.DEVICE_CONFIG_CLEANUP)),
):
    """清理设备的旧配置快照"""
    if cleanup_data.device_id:
        # 清理单个设备
        result = await service.cleanup_old_configs(
            cleanup_data.device_id, operation_context, cleanup_data.keep_latest_count
        )
        deleted_count = result["deleted_count"]
    else:
        # TODO: 实现清理所有设备的逻辑
        deleted_count = 0

    return DeviceConfigCleanupResponse(
        deleted_count=deleted_count,
        freed_space=deleted_count * 1024,  # 估算释放空间
    )


@router.post("/cleanup/device/{device_id}", response_model=SuccessResponse, summary="清理指定设备旧配置")
async def cleanup_device_configs(
    device_id: UUID,
    keep_count: int = Query(default=50, description="保留配置数量", ge=1, le=100),
    service: DeviceConfigService = Depends(get_device_config_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.DEVICE_CONFIG_CLEANUP)),
):
    """清理指定设备的旧配置快照"""
    result = await service.cleanup_old_configs(device_id, operation_context, keep_count)
    return SuccessResponse(message=result["message"])


# ===== 统计和搜索功能 =====


@router.get("/statistics", response_model=dict[str, Any], summary="获取配置快照统计")
async def get_config_statistics(
    device_id: UUID | None = Query(default=None, description="设备ID筛选"),
    service: DeviceConfigService = Depends(get_device_config_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.DEVICE_CONFIG_READ)),
):
    """获取配置快照的统计信息"""
    return await service.get_config_statistics(device_id)


@router.get("/search", response_model=list[DeviceConfigResponse], summary="搜索配置快照")
async def search_device_configs(
    device_id: UUID | None = Query(default=None, description="设备ID"),
    config_type: str | None = Query(default=None, description="配置类型"),
    backup_by: UUID | None = Query(default=None, description="备份人ID"),
    service: DeviceConfigService = Depends(get_device_config_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.DEVICE_CONFIG_READ)),
):
    """搜索配置快照"""
    configs = await service.search_configs(
        device_id=device_id,
        config_type=config_type,
        backup_by=backup_by,
    )
    return [DeviceConfigResponse.model_validate(config) for config in configs]


@router.get("/recent", response_model=list[DeviceConfigResponse], summary="获取最近配置")
async def get_recent_configs(
    days: int = Query(default=7, description="查询天数", ge=1, le=365),
    limit: int = Query(default=100, description="返回数量限制", ge=1, le=500),
    service: DeviceConfigService = Depends(get_device_config_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.DEVICE_CONFIG_READ)),
):
    """获取最近的配置快照"""
    configs = await service.get_recent_configs(days, limit)
    return [DeviceConfigResponse.model_validate(config) for config in configs]


@router.get("/user/{user_id}", response_model=list[DeviceConfigResponse], summary="获取用户配置快照")
async def get_user_configs(
    user_id: UUID,
    limit: int = Query(default=100, description="返回数量限制", ge=1, le=500),
    service: DeviceConfigService = Depends(get_device_config_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.DEVICE_CONFIG_READ)),
):
    """获取用户备份的配置快照"""
    configs = await service.get_user_configs(user_id, limit)
    return [DeviceConfigResponse.model_validate(config) for config in configs]


# ===== 配置验证功能 =====


@router.post("/validate", response_model=dict[str, Any], summary="验证配置内容")
async def validate_config_content(
    config_content: str,
    config_type: str = Query(description="配置类型"),
    service: DeviceConfigService = Depends(get_device_config_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.DEVICE_CONFIG_READ)),
):
    """验证配置内容的有效性"""
    return await service.validate_config_content(config_content, config_type)
