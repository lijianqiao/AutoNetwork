"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: region.py
@DateTime: 2025/07/23
@Docs: 基地管理相关的Pydantic模型
"""

from pydantic import BaseModel, Field

from app.schemas.base import (
    ListQueryRequest,
    ORMBase,
    PaginatedResponse,
)


class RegionBase(ORMBase):
    """基地基础字段"""

    region_code: str = Field(description="基地代码", min_length=2, max_length=50)
    region_name: str = Field(description="基地名称", min_length=2, max_length=100)
    snmp_community: str = Field(description="SNMP社区字符串", min_length=1, max_length=200)
    description: str | None = Field(default=None, description="描述", max_length=1000)


class RegionCreateRequest(BaseModel):
    """创建基地请求"""

    region_code: str = Field(description="基地代码", min_length=2, max_length=50)
    region_name: str = Field(description="基地名称", min_length=2, max_length=100)
    snmp_community: str = Field(description="SNMP社区字符串", min_length=1, max_length=200)
    description: str | None = Field(default=None, description="描述", max_length=1000)


class RegionUpdateRequest(BaseModel):
    """更新基地请求"""

    region_name: str | None = Field(default=None, description="基地名称", min_length=2, max_length=100)
    snmp_community: str | None = Field(default=None, description="SNMP社区字符串", min_length=1, max_length=200)
    description: str | None = Field(default=None, description="描述", max_length=1000)
    version: int | None = Field(default=None, description="数据版本号，用于乐观锁")


class RegionResponse(RegionBase):
    """基地响应（用于列表）"""

    device_count: int = Field(default=0, description="关联的设备数量")


class RegionDetailResponse(RegionBase):
    """基地详情响应"""

    pass


class RegionListRequest(ListQueryRequest):
    """基地列表查询请求"""

    region_code: str | None = Field(default=None, description="基地代码筛选")


class RegionListResponse(PaginatedResponse[RegionResponse]):
    """基地列表响应"""

    pass
