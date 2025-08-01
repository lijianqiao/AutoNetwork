"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: unified_query.py
@DateTime: 2025/08/01
@Docs: 统一查询接口的Pydantic模型 - 支持所有查询类型的统一入口
"""

from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field


class UnifiedQueryRequest(BaseModel):
    """统一查询请求 - 支持所有查询类型的统一入口"""

    query_type: Literal["template", "template_type", "mac_address", "interface_status", "custom_command"] = Field(
        description="查询类型"
    )
    device_ids: list[UUID] = Field(description="目标设备ID列表", min_length=1)
    parameters: dict[str, Any] | None = Field(default=None, description="查询参数")

    # 模板相关参数
    template_id: UUID | None = Field(default=None, description="查询模板ID（template类型必需）")
    template_type: str | None = Field(default=None, description="模板类型（template_type类型必需）")
    template_version: int | None = Field(default=None, description="指定模板版本（None为最新版本）")
    enable_parsing: bool = Field(default=True, description="是否启用结果解析")
    custom_template: str | None = Field(default=None, description="自定义TextFSM模板名称")

    # 执行参数
    timeout: int = Field(default=30, description="查询超时(秒)", ge=5, le=300)
    max_concurrent: int = Field(default=10, description="最大并发数", ge=1, le=50)


class UnifiedQueryResult(BaseModel):
    """统一查询结果"""

    device_id: UUID | None = Field(default=None, description="设备ID")
    hostname: str = Field(description="设备主机名")
    ip_address: str = Field(description="设备IP地址")
    success: bool = Field(description="查询是否成功")
    result_data: dict[str, Any] | None = Field(default=None, description="查询结果数据")
    raw_output: str | None = Field(default=None, description="原始输出")
    error_message: str | None = Field(default=None, description="错误信息")
    execution_time: float = Field(description="执行耗时(秒)", ge=0)


class UnifiedQuerySummary(BaseModel):
    """统一查询摘要"""

    total_devices: int = Field(description="总设备数")
    successful_devices: int = Field(description="成功设备数")
    failed_devices: int = Field(description="失败设备数")
    total_execution_time: float = Field(description="总执行时间(秒)")
    average_execution_time: float = Field(description="平均执行时间(秒)")


class UnifiedQueryResponse(BaseModel):
    """统一查询响应"""

    query_id: UUID = Field(description="查询ID")
    query_type: str = Field(description="查询类型")
    device_results: list[UnifiedQueryResult] = Field(description="设备查询结果列表")
    summary: UnifiedQuerySummary = Field(description="查询摘要")
    execution_time: float = Field(description="总执行时间(秒)")
    created_at: str = Field(description="查询创建时间")


# 向后兼容的便捷请求类型
class MacQueryConvenienceRequest(BaseModel):
    """MAC地址查询便捷请求"""

    device_ids: list[UUID] = Field(description="目标设备ID列表", min_length=1)
    mac_address: str = Field(description="要查询的MAC地址", min_length=12, max_length=17)
    enable_parsing: bool = Field(default=True, description="是否启用结果解析")
    timeout: int = Field(default=30, description="查询超时(秒)", ge=5, le=300)

    def to_unified_request(self) -> UnifiedQueryRequest:
        """转换为统一查询请求"""
        return UnifiedQueryRequest(
            query_type="mac_address",
            device_ids=self.device_ids,
            parameters={"mac_address": self.mac_address},
            enable_parsing=self.enable_parsing,
            timeout=self.timeout,
        )


class InterfaceStatusQueryConvenienceRequest(BaseModel):
    """接口状态查询便捷请求"""

    device_ids: list[UUID] = Field(description="目标设备ID列表", min_length=1)
    interface_pattern: str | None = Field(default=None, description="接口模式（可选）")
    enable_parsing: bool = Field(default=True, description="是否启用结果解析")
    timeout: int = Field(default=30, description="查询超时(秒)", ge=5, le=300)

    def to_unified_request(self) -> UnifiedQueryRequest:
        """转换为统一查询请求"""
        parameters = {}
        if self.interface_pattern:
            parameters["interface_pattern"] = self.interface_pattern

        return UnifiedQueryRequest(
            query_type="interface_status",
            device_ids=self.device_ids,
            parameters=parameters if parameters else None,
            enable_parsing=self.enable_parsing,
            timeout=self.timeout,
        )


class CustomCommandQueryConvenienceRequest(BaseModel):
    """自定义命令查询便捷请求"""

    device_ids: list[UUID] = Field(description="目标设备ID列表", min_length=1)
    command: str = Field(description="要执行的命令", min_length=1, max_length=500)
    enable_parsing: bool = Field(default=False, description="是否启用结果解析")
    timeout: int = Field(default=30, description="查询超时(秒)", ge=5, le=300)

    def to_unified_request(self) -> UnifiedQueryRequest:
        """转换为统一查询请求"""
        return UnifiedQueryRequest(
            query_type="custom_command",
            device_ids=self.device_ids,
            parameters={"command": self.command},
            enable_parsing=self.enable_parsing,
            timeout=self.timeout,
        )


# 向后兼容的旧类名（别名）
MacQueryUnifiedRequest = MacQueryConvenienceRequest
InterfaceStatusUnifiedRequest = InterfaceStatusQueryConvenienceRequest
CustomCommandUnifiedRequest = CustomCommandQueryConvenienceRequest
