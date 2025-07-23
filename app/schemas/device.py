"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: device.py
@DateTime: 2025/07/23
@Docs: 网络设备管理相关的Pydantic模型
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, IPvAnyAddress

from app.schemas.base import (
    ListQueryRequest,
    ORMBase,
    PaginatedResponse,
)
from app.schemas.region import RegionResponse
from app.schemas.types import ObjectUUID
from app.schemas.vendor import VendorResponse


class DeviceBase(ORMBase):
    """设备基础字段"""

    hostname: str = Field(description="设备主机名", min_length=2, max_length=100)
    ip_address: str = Field(description="管理IP地址", min_length=7, max_length=45)
    device_type: str = Field(description="设备类型", min_length=2, max_length=50)
    network_layer: str = Field(description="网络层级", min_length=2, max_length=50)
    vendor_id: ObjectUUID = Field(description="关联厂商ID")
    region_id: ObjectUUID = Field(description="关联基地ID")
    model: str = Field(description="设备型号", min_length=1, max_length=100)
    serial_number: str = Field(description="序列号", min_length=1, max_length=100)
    location: str = Field(description="物理位置", min_length=1, max_length=200)
    auth_type: Literal["dynamic", "static"] = Field(description="认证类型")
    static_username: str | None = Field(default=None, description="静态用户名", max_length=200)
    static_password: str | None = Field(default=None, description="静态密码", max_length=200)
    ssh_port: int = Field(default=22, description="SSH端口", ge=1, le=65535)
    is_active: bool = Field(default=True, description="是否在用")
    last_connected_at: datetime | None = Field(default=None, description="最后连接时间")


class DeviceCreateRequest(BaseModel):
    """创建设备请求"""

    hostname: str = Field(description="设备主机名", min_length=2, max_length=100)
    ip_address: IPvAnyAddress = Field(description="管理IP地址")
    device_type: str = Field(description="设备类型", min_length=2, max_length=50)
    network_layer: str = Field(description="网络层级", min_length=2, max_length=50)
    vendor_id: ObjectUUID = Field(description="关联厂商ID")
    region_id: ObjectUUID = Field(description="关联基地ID")
    model: str = Field(description="设备型号", min_length=1, max_length=100)
    serial_number: str = Field(description="序列号", min_length=1, max_length=100)
    location: str = Field(description="物理位置", min_length=1, max_length=200)
    auth_type: Literal["dynamic", "static"] = Field(description="认证类型")
    static_username: str | None = Field(default=None, description="静态用户名", max_length=200)
    static_password: str | None = Field(default=None, description="静态密码", max_length=200)
    ssh_port: int = Field(default=22, description="SSH端口", ge=1, le=65535)


class DeviceUpdateRequest(BaseModel):
    """更新设备请求"""

    hostname: str | None = Field(default=None, description="设备主机名", min_length=2, max_length=100)
    ip_address: IPvAnyAddress | None = Field(default=None, description="管理IP地址")
    device_type: str | None = Field(default=None, description="设备类型", min_length=2, max_length=50)
    network_layer: str | None = Field(default=None, description="网络层级", min_length=2, max_length=50)
    vendor_id: ObjectUUID | None = Field(default=None, description="关联厂商ID")
    region_id: ObjectUUID | None = Field(default=None, description="关联基地ID")
    model: str | None = Field(default=None, description="设备型号", min_length=1, max_length=100)
    serial_number: str | None = Field(default=None, description="序列号", min_length=1, max_length=100)
    location: str | None = Field(default=None, description="物理位置", min_length=1, max_length=200)
    auth_type: Literal["dynamic", "static"] | None = Field(default=None, description="认证类型")
    static_username: str | None = Field(default=None, description="静态用户名", max_length=200)
    static_password: str | None = Field(default=None, description="静态密码", max_length=200)
    ssh_port: int | None = Field(default=None, description="SSH端口", ge=1, le=65535)
    is_active: bool | None = Field(default=None, description="是否在用")
    version: int | None = Field(default=None, description="数据版本号，用于乐观锁")


class DeviceResponse(DeviceBase):
    """设备响应（用于列表）"""

    vendor: VendorResponse | None = Field(default=None, description="关联厂商信息")
    region: RegionResponse | None = Field(default=None, description="关联基地信息")


class DeviceDetailResponse(DeviceBase):
    """设备详情响应"""

    vendor: VendorResponse = Field(description="关联厂商信息")
    region: RegionResponse = Field(description="关联基地信息")


class DeviceListRequest(ListQueryRequest):
    """设备列表查询请求"""

    hostname: str | None = Field(default=None, description="设备主机名筛选")
    ip_address: str | None = Field(default=None, description="IP地址筛选")
    device_type: str | None = Field(default=None, description="设备类型筛选")
    network_layer: str | None = Field(default=None, description="网络层级筛选")
    vendor_id: ObjectUUID | None = Field(default=None, description="厂商ID筛选")
    region_id: ObjectUUID | None = Field(default=None, description="基地ID筛选")
    auth_type: Literal["dynamic", "static"] | None = Field(default=None, description="认证类型筛选")


class DeviceListResponse(PaginatedResponse[DeviceResponse]):
    """设备列表响应"""

    pass


class DeviceConnectionTestRequest(BaseModel):
    """设备连接测试请求"""

    device_ids: list[ObjectUUID] = Field(description="设备ID列表", min_length=1)
    username: str | None = Field(default=None, description="动态密码用户名", max_length=100)
    password: str | None = Field(default=None, description="动态密码", max_length=200)


class DeviceConnectionResult(BaseModel):
    """设备连接结果"""

    device_id: ObjectUUID = Field(description="设备ID")
    hostname: str = Field(description="设备主机名")
    ip_address: str = Field(description="IP地址")
    success: bool = Field(description="连接是否成功")
    error_message: str | None = Field(default=None, description="错误信息")
    connection_time: float | None = Field(default=None, description="连接耗时(秒)")


class DeviceConnectionTestResponse(BaseModel):
    """设备连接测试响应"""

    code: int = Field(default=200, description="响应代码")
    message: str = Field(default="连接测试完成", description="响应消息")
    total_count: int = Field(description="总设备数")
    success_count: int = Field(description="成功连接数")
    failed_count: int = Field(description="失败连接数")
    results: list[DeviceConnectionResult] = Field(description="详细结果")


class DeviceBatchOperationRequest(BaseModel):
    """设备批量操作请求"""

    device_ids: list[ObjectUUID] = Field(description="设备ID列表", min_length=1)
    operation: Literal["activate", "deactivate", "delete"] = Field(description="操作类型")


class DeviceAuthTypeUpdateRequest(BaseModel):
    """设备认证类型更新请求"""

    auth_type: Literal["dynamic", "static"] = Field(description="认证类型")
    static_username: str | None = Field(default=None, description="静态用户名", max_length=200)
    static_password: str | None = Field(default=None, description="静态密码", max_length=200)
