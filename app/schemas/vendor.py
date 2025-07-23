"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: vendor.py
@DateTime: 2025/07/23
@Docs: 设备厂商管理相关的Pydantic模型
"""

from pydantic import BaseModel, Field

from app.schemas.base import (
    ListQueryRequest,
    ORMBase,
    PaginatedResponse,
)


class VendorBase(ORMBase):
    """厂商基础字段"""

    vendor_code: str = Field(description="厂商代码", min_length=2, max_length=50)
    vendor_name: str = Field(description="厂商名称", min_length=2, max_length=100)
    scrapli_platform: str = Field(description="Scrapli平台标识", min_length=2, max_length=100)
    default_ssh_port: int = Field(default=22, description="默认SSH端口", ge=1, le=65535)
    connection_timeout: int = Field(default=30, description="连接超时(秒)", ge=1, le=300)
    command_timeout: int = Field(default=10, description="命令超时(秒)", ge=1, le=120)


class VendorCreateRequest(BaseModel):
    """创建厂商请求"""

    vendor_code: str = Field(description="厂商代码", min_length=2, max_length=50)
    vendor_name: str = Field(description="厂商名称", min_length=2, max_length=100)
    scrapli_platform: str = Field(description="Scrapli平台标识", min_length=2, max_length=100)
    default_ssh_port: int = Field(default=22, description="默认SSH端口", ge=1, le=65535)
    connection_timeout: int = Field(default=30, description="连接超时(秒)", ge=1, le=300)
    command_timeout: int = Field(default=10, description="命令超时(秒)", ge=1, le=120)


class VendorUpdateRequest(BaseModel):
    """更新厂商请求"""

    vendor_name: str | None = Field(default=None, description="厂商名称", min_length=2, max_length=100)
    scrapli_platform: str | None = Field(default=None, description="Scrapli平台标识", min_length=2, max_length=100)
    default_ssh_port: int | None = Field(default=None, description="默认SSH端口", ge=1, le=65535)
    connection_timeout: int | None = Field(default=None, description="连接超时(秒)", ge=1, le=300)
    command_timeout: int | None = Field(default=None, description="命令超时(秒)", ge=1, le=120)
    version: int | None = Field(default=None, description="数据版本号，用于乐观锁")


class VendorResponse(VendorBase):
    """厂商响应（用于列表）"""

    device_count: int = Field(default=0, description="关联的设备数量")
    command_count: int = Field(default=0, description="关联的命令数量")


class VendorDetailResponse(VendorBase):
    """厂商详情响应"""

    pass


class VendorListRequest(ListQueryRequest):
    """厂商列表查询请求"""

    vendor_code: str | None = Field(default=None, description="厂商代码筛选")
    scrapli_platform: str | None = Field(default=None, description="Scrapli平台筛选")


class VendorListResponse(PaginatedResponse[VendorResponse]):
    """厂商列表响应"""

    pass
