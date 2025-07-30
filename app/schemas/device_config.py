"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: device_config.py
@DateTime: 2025/07/23
@Docs: 设备配置快照管理相关的Pydantic模型
"""

from typing import Any, Literal

from pydantic import BaseModel, Field

from app.schemas.base import (
    ListQueryRequest,
    ORMBase,
    PaginatedResponse,
)
from app.schemas.device import DeviceResponse
from app.schemas.types import ObjectUUID
from app.schemas.user import UserResponse


class DeviceConfigBase(ORMBase):
    """设备配置基础字段"""

    device_id: ObjectUUID = Field(description="关联设备ID")
    config_type: Literal["running", "startup"] = Field(description="配置类型")
    config_content: str = Field(description="配置内容", min_length=1)
    config_hash: str = Field(description="配置哈希值", min_length=32, max_length=64)
    backup_by_id: ObjectUUID | None = Field(default=None, description="备份人ID")
    backup_reason: str | None = Field(default=None, description="备份原因", max_length=1000)


class DeviceConfigCreateRequest(BaseModel):
    """创建设备配置请求"""

    device_id: ObjectUUID = Field(description="关联设备ID")
    config_type: Literal["running", "startup"] = Field(description="配置类型")
    config_content: str = Field(description="配置内容", min_length=1)
    backup_reason: str | None = Field(default=None, description="备份原因", max_length=1000)


class DeviceConfigUpdateRequest(BaseModel):
    """更新设备配置请求"""

    backup_reason: str | None = Field(default=None, description="备份原因", max_length=1000)
    version: int | None = Field(default=None, description="数据版本号，用于乐观锁")


class DeviceConfigResponse(DeviceConfigBase):
    """设备配置响应（用于列表）"""

    device: DeviceResponse | None = Field(default=None, description="关联设备信息")
    backup_by: UserResponse | None = Field(default=None, description="备份人信息")
    config_size: int = Field(default=0, description="配置大小(字节)")


class DeviceConfigDetailResponse(DeviceConfigBase):
    """设备配置详情响应"""

    device: DeviceResponse = Field(description="关联设备信息")
    backup_by: UserResponse | None = Field(default=None, description="备份人信息")
    config_size: int = Field(description="配置大小(字节)")


class DeviceConfigListRequest(ListQueryRequest):
    """设备配置列表查询请求"""

    device_id: ObjectUUID | None = Field(default=None, description="设备ID筛选")
    config_type: Literal["running", "startup"] | None = Field(default=None, description="配置类型筛选")
    backup_by_id: ObjectUUID | None = Field(default=None, description="备份人ID筛选")
    config_hash: str | None = Field(default=None, description="配置哈希值筛选")


class DeviceConfigListResponse(PaginatedResponse[DeviceConfigResponse]):
    """设备配置列表响应"""

    pass


class DeviceConfigCompareRequest(BaseModel):
    """设备配置对比请求"""

    config1_id: ObjectUUID = Field(description="配置1的ID")
    config2_id: ObjectUUID = Field(description="配置2的ID")


class DeviceConfigDifference(BaseModel):
    """配置差异项"""

    line_number: int = Field(description="行号")
    change_type: Literal["added", "removed", "modified"] = Field(description="变更类型")
    old_content: str | None = Field(default=None, description="原内容")
    new_content: str | None = Field(default=None, description="新内容")


class DeviceConfigCompareResponse(BaseModel):
    """设备配置对比响应"""

    code: int = Field(default=200, description="响应代码")
    message: str = Field(default="对比完成", description="响应消息")
    config1_info: DeviceConfigResponse = Field(description="配置1信息")
    config2_info: DeviceConfigResponse = Field(description="配置2信息")
    is_identical: bool = Field(description="配置是否相同")
    differences: list[DeviceConfigDifference] = Field(description="差异列表")
    added_lines: int = Field(description="新增行数")
    removed_lines: int = Field(description="删除行数")
    modified_lines: int = Field(description="修改行数")


class DeviceConfigBackupRequest(BaseModel):
    """设备配置备份请求"""

    device_ids: list[ObjectUUID] = Field(description="设备ID列表", min_length=1)
    config_type: Literal["running", "startup", "both"] = Field(description="配置类型")
    backup_reason: str | None = Field(default=None, description="备份原因", max_length=1000)
    username: str | None = Field(default=None, description="动态密码用户名", max_length=100)
    password: str | None = Field(default=None, description="动态密码", max_length=200)


class DeviceConfigBackupResult(BaseModel):
    """设备配置备份结果"""

    device_id: ObjectUUID = Field(description="设备ID")
    hostname: str = Field(description="设备主机名")
    success: bool = Field(description="备份是否成功")
    config_ids: list[ObjectUUID] = Field(description="备份的配置ID列表")
    error_message: str | None = Field(default=None, description="错误信息")


class DeviceConfigBackupResponse(BaseModel):
    """设备配置备份响应"""

    code: int = Field(default=200, description="响应代码")
    message: str = Field(default="备份完成", description="响应消息")
    total_count: int = Field(description="总设备数")
    success_count: int = Field(description="成功备份数")
    failed_count: int = Field(description="失败备份数")
    results: list[DeviceConfigBackupResult] = Field(description="详细结果")


class DeviceConfigCleanupRequest(BaseModel):
    """设备配置清理请求"""

    device_id: ObjectUUID | None = Field(default=None, description="设备ID，为空则清理所有设备")
    days_to_keep: int = Field(description="保留天数", ge=1, le=365)
    keep_latest_count: int = Field(description="每个设备保留的最新配置数量", ge=1, le=100)


class DeviceConfigCleanupResponse(BaseModel):
    """设备配置清理响应"""

    code: int = Field(default=200, description="响应代码")
    message: str = Field(default="清理完成", description="响应消息")
    deleted_count: int = Field(description="删除配置数")
    freed_space: int = Field(description="释放空间(字节)")


class DeviceLatestConfigRequest(BaseModel):
    """获取设备最新配置请求"""

    device_id: ObjectUUID = Field(description="设备ID")
    config_type: Literal["running", "startup"] = Field(description="配置类型")


class DeviceConfigHistoryRequest(BaseModel):
    """设备配置历史请求"""

    device_id: ObjectUUID = Field(description="设备ID")
    config_type: Literal["running", "startup"] | None = Field(default=None, description="配置类型筛选")
    limit: int = Field(default=10, description="返回数量限制", ge=1, le=100)


# ===== 智能配置差异分析相关Schema =====


class SmartConfigCompareRequest(BaseModel):
    """智能配置对比请求"""

    config1_id: ObjectUUID = Field(description="配置1的ID")
    config2_id: ObjectUUID = Field(description="配置2的ID")
    ignore_whitespace: bool = Field(default=True, description="是否忽略空白字符差异")
    ignore_comments: bool = Field(default=False, description="是否忽略注释行差异")
    context_lines: int = Field(default=3, description="上下文行数", ge=0, le=10)


class ConfigDiffLine(BaseModel):
    """配置差异行"""

    line_number: int = Field(description="行号")
    content: str = Field(description="行内容")
    diff_type: Literal["added", "removed", "modified", "moved", "unchanged"] = Field(description="差异类型")
    section: Literal["interface", "routing", "access-list", "vlan", "system", "security", "qos", "other"] = Field(
        description="配置段落类型"
    )
    indent_level: int = Field(description="缩进级别")
    is_comment: bool = Field(description="是否为注释行")
    original_line_number: int | None = Field(default=None, description="原始行号（用于moved类型）")


class ConfigSideBySideDiff(BaseModel):
    """并排差异视图项"""

    left_line_no: int | None = Field(description="左侧行号")
    right_line_no: int | None = Field(description="右侧行号")
    left_content: str = Field(description="左侧内容")
    right_content: str = Field(description="右侧内容")
    type: Literal["equal", "delete", "insert", "replace"] = Field(description="差异类型")


class ConfigDiffSummary(BaseModel):
    """配置差异摘要"""

    total_differences: int = Field(description="总差异行数")
    lines_added: int = Field(description="新增行数")
    lines_removed: int = Field(description="删除行数")
    lines_modified: int = Field(description="修改行数")
    sections_affected: int = Field(description="受影响的段落数")
    section_statistics: dict[str, dict[str, int]] = Field(description="各段落统计信息")
    similarity_ratio: float = Field(description="相似度比例", ge=0.0, le=1.0)
    is_identical: bool = Field(description="是否完全相同")


class SmartConfigCompareResponse(BaseModel):
    """智能配置对比响应"""

    config1_info: dict[str, Any] = Field(description="配置1信息")
    config2_info: dict[str, Any] = Field(description="配置2信息")
    diff_lines: list[ConfigDiffLine] = Field(description="差异行列表")
    summary: ConfigDiffSummary = Field(description="差异摘要")
    sections_changed: list[str] = Field(description="变更的配置段落")
    unified_diff: str = Field(description="统一差异格式")
    side_by_side_diff: list[ConfigSideBySideDiff] = Field(description="并排差异视图")


class CompareWithLatestRequest(BaseModel):
    """与最新配置对比请求"""

    config_id: ObjectUUID = Field(description="要对比的配置快照ID")
    ignore_whitespace: bool = Field(default=True, description="是否忽略空白字符差异")
    ignore_comments: bool = Field(default=False, description="是否忽略注释行差异")


class ConfigDiffSummaryRequest(BaseModel):
    """配置差异摘要请求"""

    device_id: ObjectUUID = Field(description="设备ID")
    days: int = Field(default=30, description="查看最近几天的变更", ge=1, le=365)
    config_type: Literal["running", "startup"] = Field(default="running", description="配置类型")


class ConfigChangePoint(BaseModel):
    """配置变更点"""

    from_config_id: str = Field(description="变更前配置ID")
    to_config_id: str = Field(description="变更后配置ID")
    change_time: str | None = Field(description="变更时间")
    backup_reason: str | None = Field(description="备份原因")


class ConfigDiffSummaryResponse(BaseModel):
    """配置差异摘要响应"""

    device_id: str = Field(description="设备ID")
    config_type: str = Field(description="配置类型")
    days: int = Field(description="查看天数")
    total_snapshots: int = Field(description="总快照数")
    total_changes: int = Field(description="总变更次数")
    has_changes: bool = Field(description="是否有变更")
    latest_config: dict[str, Any] = Field(description="最新配置信息")
    oldest_config: dict[str, Any] = Field(description="最旧配置信息")
    overall_diff_summary: ConfigDiffSummary = Field(description="整体差异摘要")
    change_points: list[ConfigChangePoint] = Field(description="变更点列表")
    sections_changed: list[str] = Field(description="变更的配置段落")
    message: str | None = Field(default=None, description="提示信息")


class BatchConfigCompareRequest(BaseModel):
    """批量配置对比请求"""

    comparison_pairs: list[tuple[ObjectUUID, ObjectUUID]] = Field(
        description="配置对比对列表", min_length=1, max_length=50
    )
    ignore_whitespace: bool = Field(default=True, description="是否忽略空白字符差异")
    ignore_comments: bool = Field(default=False, description="是否忽略注释行差异")


class BatchConfigCompareResult(BaseModel):
    """批量配置对比结果项"""

    index: int = Field(description="对比索引")
    config1_id: str = Field(description="配置1 ID")
    config2_id: str = Field(description="配置2 ID")
    success: bool = Field(description="对比是否成功")
    summary: ConfigDiffSummary | None = Field(default=None, description="差异摘要")
    sections_changed: list[str] | None = Field(default=None, description="变更的配置段落")
    error: str | None = Field(default=None, description="错误信息")


class BatchConfigCompareResponse(BaseModel):
    """批量配置对比响应"""

    total_comparisons: int = Field(description="总对比数")
    successful_comparisons: int = Field(description="成功对比数")
    failed_comparisons: int = Field(description="失败对比数")
    results: list[BatchConfigCompareResult] = Field(description="详细结果列表")


class ExportDiffToHtmlRequest(BaseModel):
    """导出差异为HTML请求"""

    config1_id: ObjectUUID = Field(description="配置1的ID")
    config2_id: ObjectUUID = Field(description="配置2的ID")
    ignore_whitespace: bool = Field(default=True, description="是否忽略空白字符差异")
    ignore_comments: bool = Field(default=False, description="是否忽略注释行差异")
