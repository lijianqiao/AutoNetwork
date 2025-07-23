"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: query_template.py
@DateTime: 2025/07/23
@Docs: 查询模板管理相关的Pydantic模型
"""

from pydantic import BaseModel, Field

from app.schemas.base import (
    ListQueryRequest,
    ORMBase,
    PaginatedResponse,
)
from app.schemas.types import ObjectUUID


class QueryTemplateBase(ORMBase):
    """查询模板基础字段"""

    template_name: str = Field(description="模板名称", min_length=2, max_length=100)
    template_type: str = Field(description="模板类型", min_length=2, max_length=50)
    description: str | None = Field(default=None, description="描述", max_length=1000)
    is_active: bool = Field(default=True, description="是否启用")


class QueryTemplateCreateRequest(BaseModel):
    """创建查询模板请求"""

    template_name: str = Field(description="模板名称", min_length=2, max_length=100)
    template_type: str = Field(description="模板类型", min_length=2, max_length=50)
    description: str | None = Field(default=None, description="描述", max_length=1000)


class QueryTemplateUpdateRequest(BaseModel):
    """更新查询模板请求"""

    template_name: str | None = Field(default=None, description="模板名称", min_length=2, max_length=100)
    description: str | None = Field(default=None, description="描述", max_length=1000)
    is_active: bool | None = Field(default=None, description="是否启用")
    version: int | None = Field(default=None, description="数据版本号，用于乐观锁")


class QueryTemplateResponse(QueryTemplateBase):
    """查询模板响应（用于列表）"""

    command_count: int = Field(default=0, description="关联的命令数量")


class QueryTemplateDetailResponse(QueryTemplateBase):
    """查询模板详情响应"""

    pass


class QueryTemplateListRequest(ListQueryRequest):
    """查询模板列表查询请求"""

    template_type: str | None = Field(default=None, description="模板类型筛选")


class QueryTemplateListResponse(PaginatedResponse[QueryTemplateResponse]):
    """查询模板列表响应"""

    pass


class QueryTemplateActivateRequest(BaseModel):
    """激活/停用模板请求"""

    template_ids: list[ObjectUUID] = Field(description="模板ID列表", min_length=1)
    is_active: bool = Field(description="是否激活")
