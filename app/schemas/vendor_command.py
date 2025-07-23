"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: vendor_command.py
@DateTime: 2025/07/23
@Docs: 厂商命令管理相关的Pydantic模型
"""

from typing import Any

from pydantic import BaseModel, Field

from app.schemas.base import (
    ListQueryRequest,
    ORMBase,
    PaginatedResponse,
)
from app.schemas.query_template import QueryTemplateResponse
from app.schemas.types import ObjectUUID
from app.schemas.vendor import VendorResponse


class VendorCommandBase(ORMBase):
    """厂商命令基础字段"""

    template_id: ObjectUUID = Field(description="关联查询模板ID")
    vendor_id: ObjectUUID = Field(description="关联厂商ID")
    commands: list[str] = Field(description="命令列表")
    parser_type: str = Field(description="解析器类型", min_length=2, max_length=50)
    parser_template: str = Field(description="解析模板内容", min_length=1)


class VendorCommandCreateRequest(BaseModel):
    """创建厂商命令请求"""

    template_id: ObjectUUID = Field(description="关联查询模板ID")
    vendor_id: ObjectUUID = Field(description="关联厂商ID")
    commands: list[str] = Field(description="命令列表", min_length=1)
    parser_type: str = Field(description="解析器类型", min_length=2, max_length=50)
    parser_template: str = Field(description="解析模板内容", min_length=1)


class VendorCommandUpdateRequest(BaseModel):
    """更新厂商命令请求"""

    commands: list[str] | None = Field(default=None, description="命令列表", min_length=1)
    parser_type: str | None = Field(default=None, description="解析器类型", min_length=2, max_length=50)
    parser_template: str | None = Field(default=None, description="解析模板内容", min_length=1)
    version: int | None = Field(default=None, description="数据版本号，用于乐观锁")


class VendorCommandResponse(VendorCommandBase):
    """厂商命令响应（用于列表）"""

    template: QueryTemplateResponse | None = Field(default=None, description="关联查询模板信息")
    vendor: VendorResponse | None = Field(default=None, description="关联厂商信息")


class VendorCommandDetailResponse(VendorCommandBase):
    """厂商命令详情响应"""

    template: QueryTemplateResponse = Field(description="关联查询模板信息")
    vendor: VendorResponse = Field(description="关联厂商信息")


class VendorCommandListRequest(ListQueryRequest):
    """厂商命令列表查询请求"""

    template_id: ObjectUUID | None = Field(default=None, description="查询模板ID筛选")
    vendor_id: ObjectUUID | None = Field(default=None, description="厂商ID筛选")
    parser_type: str | None = Field(default=None, description="解析器类型筛选")


class VendorCommandListResponse(PaginatedResponse[VendorCommandResponse]):
    """厂商命令列表响应"""

    pass


class VendorCommandBatchCreateRequest(BaseModel):
    """批量创建厂商命令请求"""

    template_id: ObjectUUID = Field(description="关联查询模板ID")
    commands: list[dict[str, Any]] = Field(description="厂商命令列表", min_length=1)


class VendorCommandBatchCreateItem(BaseModel):
    """批量创建厂商命令项"""

    vendor_id: ObjectUUID = Field(description="关联厂商ID")
    commands: list[str] = Field(description="命令列表", min_length=1)
    parser_type: str = Field(description="解析器类型", min_length=2, max_length=50)
    parser_template: str = Field(description="解析模板内容", min_length=1)


class VendorCommandCheckRequest(BaseModel):
    """检查厂商命令存在性请求"""

    template_id: ObjectUUID = Field(description="查询模板ID")
    vendor_id: ObjectUUID = Field(description="厂商ID")


class VendorCommandExistsResponse(BaseModel):
    """厂商命令存在性响应"""

    code: int = Field(default=200, description="响应代码")
    message: str = Field(default="检查完成", description="响应消息")
    exists: bool = Field(description="是否存在")
    command_id: ObjectUUID | None = Field(default=None, description="存在时的命令ID")
