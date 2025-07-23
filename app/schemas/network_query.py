"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: network_query.py
@DateTime: 2025/07/23
@Docs: 网络查询相关的Pydantic模型
"""

from typing import Any, Literal

from pydantic import BaseModel, Field

from app.schemas.types import ObjectUUID


class NetworkQueryRequest(BaseModel):
    """网络查询请求"""

    query_type: str = Field(description="查询类型", min_length=2, max_length=50)
    target_devices: list[ObjectUUID] = Field(description="目标设备ID列表", min_length=1)
    query_params: dict[str, Any] = Field(description="查询参数")
    username: str | None = Field(default=None, description="动态密码用户名", max_length=100)
    password: str | None = Field(default=None, description="动态密码", max_length=200)
    timeout: int = Field(default=30, description="查询超时(秒)", ge=5, le=300)


class NetworkQueryByIPRequest(BaseModel):
    """按IP地址网络查询请求"""

    query_type: str = Field(description="查询类型", min_length=2, max_length=50)
    target_ips: list[str] = Field(description="目标设备IP列表", min_length=1)
    query_params: dict[str, Any] = Field(description="查询参数")
    username: str | None = Field(default=None, description="动态密码用户名", max_length=100)
    password: str | None = Field(default=None, description="动态密码", max_length=200)
    timeout: int = Field(default=30, description="查询超时(秒)", ge=5, le=300)


class NetworkQueryResult(BaseModel):
    """网络查询结果"""

    device_id: ObjectUUID | None = Field(default=None, description="设备ID")
    hostname: str = Field(description="设备主机名")
    ip_address: str = Field(description="设备IP地址")
    success: bool = Field(description="查询是否成功")
    result_data: dict[str, Any] | None = Field(default=None, description="查询结果数据")
    raw_output: str | None = Field(default=None, description="原始输出")
    error_message: str | None = Field(default=None, description="错误信息")
    execution_time: float = Field(description="执行耗时(秒)", ge=0)


class NetworkQueryResponse(BaseModel):
    """网络查询响应"""

    code: int = Field(default=200, description="响应代码")
    message: str = Field(default="查询完成", description="响应消息")
    query_id: str = Field(description="查询ID，用于追踪")
    total_count: int = Field(description="总设备数")
    success_count: int = Field(description="成功查询数")
    failed_count: int = Field(description="失败查询数")
    results: list[NetworkQueryResult] = Field(description="详细结果")
    total_execution_time: float = Field(description="总执行时间(秒)", ge=0)


class MacQueryRequest(BaseModel):
    """MAC地址查询请求"""

    mac_address: str = Field(description="MAC地址", min_length=12, max_length=17)
    target_devices: list[ObjectUUID] = Field(description="目标设备ID列表", min_length=1)
    username: str | None = Field(default=None, description="动态密码用户名", max_length=100)
    password: str | None = Field(default=None, description="动态密码", max_length=200)


class MacQueryResult(BaseModel):
    """MAC地址查询结果"""

    device_id: ObjectUUID | None = Field(default=None, description="设备ID")
    hostname: str = Field(description="设备主机名")
    ip_address: str = Field(description="设备IP地址")
    found: bool = Field(description="是否找到MAC")
    interface: str | None = Field(default=None, description="所在接口")
    vlan: str | None = Field(default=None, description="所在VLAN")
    port_type: str | None = Field(default=None, description="端口类型")
    port_status: str | None = Field(default=None, description="端口状态")
    error_message: str | None = Field(default=None, description="错误信息")


class InterfaceStatusQueryRequest(BaseModel):
    """接口状态查询请求"""

    target_devices: list[ObjectUUID] = Field(description="目标设备ID列表", min_length=1)
    interface_filter: str | None = Field(default=None, description="接口过滤条件", max_length=100)
    status_filter: Literal["up", "down", "admin-down"] | None = Field(default=None, description="状态过滤")
    username: str | None = Field(default=None, description="动态密码用户名", max_length=100)
    password: str | None = Field(default=None, description="动态密码", max_length=200)


class InterfaceStatus(BaseModel):
    """接口状态信息"""

    interface: str = Field(description="接口名")
    status: str = Field(description="接口状态")
    protocol: str = Field(description="协议状态")
    description: str | None = Field(default=None, description="接口描述")
    speed: str | None = Field(default=None, description="接口速率")
    duplex: str | None = Field(default=None, description="双工模式")
    vlan: str | None = Field(default=None, description="所属VLAN")


class InterfaceStatusResult(BaseModel):
    """接口状态查询结果"""

    device_id: ObjectUUID | None = Field(default=None, description="设备ID")
    hostname: str = Field(description="设备主机名")
    ip_address: str = Field(description="设备IP地址")
    success: bool = Field(description="查询是否成功")
    interfaces: list[InterfaceStatus] = Field(description="接口状态列表")
    error_message: str | None = Field(default=None, description="错误信息")


class CustomCommandQueryRequest(BaseModel):
    """自定义命令查询请求"""

    commands: list[str] = Field(description="命令列表", min_length=1)
    target_devices: list[ObjectUUID] = Field(description="目标设备ID列表", min_length=1)
    username: str | None = Field(default=None, description="动态密码用户名", max_length=100)
    password: str | None = Field(default=None, description="动态密码", max_length=200)
    timeout: int = Field(default=30, description="命令超时(秒)", ge=5, le=300)


class CommandResult(BaseModel):
    """命令执行结果"""

    command: str = Field(description="执行的命令")
    success: bool = Field(description="执行是否成功")
    output: str | None = Field(default=None, description="命令输出")
    error_message: str | None = Field(default=None, description="错误信息")
    execution_time: float = Field(description="执行耗时(秒)", ge=0)


class CustomCommandResult(BaseModel):
    """自定义命令查询结果"""

    device_id: ObjectUUID | None = Field(default=None, description="设备ID")
    hostname: str = Field(description="设备主机名")
    ip_address: str = Field(description="设备IP地址")
    success: bool = Field(description="连接是否成功")
    commands: list[CommandResult] = Field(description="命令执行结果列表")
    total_execution_time: float = Field(description="总执行时间(秒)", ge=0)
    error_message: str | None = Field(default=None, description="连接错误信息")


class NetworkQueryTemplateListRequest(BaseModel):
    """查询模板列表请求"""

    template_type: str | None = Field(default=None, description="模板类型筛选")
    vendor_id: ObjectUUID | None = Field(default=None, description="厂商ID筛选")
    is_active: bool | None = Field(default=None, description="是否启用筛选")


class AvailableQueryTemplate(BaseModel):
    """可用查询模板"""

    template_id: ObjectUUID = Field(description="模板ID")
    template_name: str = Field(description="模板名称")
    template_type: str = Field(description="模板类型")
    description: str | None = Field(default=None, description="描述")
    supported_vendors: list[str] = Field(description="支持的厂商列表")
    required_params: list[str] = Field(description="必需参数列表")


class NetworkQueryTemplateListResponse(BaseModel):
    """查询模板列表响应"""

    code: int = Field(default=200, description="响应代码")
    message: str = Field(default="获取成功", description="响应消息")
    templates: list[AvailableQueryTemplate] = Field(description="可用模板列表")
