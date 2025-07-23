"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: query_history.py
@DateTime: 2025/07/23
@Docs: 查询历史管理相关的Pydantic模型
"""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.schemas.base import (
    ListQueryRequest,
    ORMBase,
    PaginatedResponse,
    StatisticsResponse,
)
from app.schemas.types import ObjectUUID
from app.schemas.user import UserResponse


class QueryHistoryBase(ORMBase):
    """查询历史基础字段"""

    user_id: ObjectUUID = Field(description="查询用户ID")
    query_type: str = Field(description="查询类型", min_length=2, max_length=50)
    query_params: dict[str, Any] = Field(description="查询参数")
    target_devices: list[str] = Field(description="目标设备IP列表")
    execution_time: float = Field(description="执行耗时(秒)", ge=0)
    status: Literal["success", "partial", "failed"] = Field(description="状态")
    error_message: str | None = Field(default=None, description="错误信息", max_length=2000)


class QueryHistoryCreateRequest(BaseModel):
    """创建查询历史请求"""

    query_type: str = Field(description="查询类型", min_length=2, max_length=50)
    query_params: dict[str, Any] = Field(description="查询参数")
    target_devices: list[str] = Field(description="目标设备IP列表", min_length=1)
    execution_time: float = Field(description="执行耗时(秒)", ge=0)
    status: Literal["success", "partial", "failed"] = Field(description="状态")
    error_message: str | None = Field(default=None, description="错误信息", max_length=2000)


class QueryHistoryResponse(QueryHistoryBase):
    """查询历史响应（用于列表）"""

    user: UserResponse | None = Field(default=None, description="查询用户信息")


class QueryHistoryDetailResponse(QueryHistoryBase):
    """查询历史详情响应"""

    user: UserResponse = Field(description="查询用户信息")


class QueryHistoryListRequest(ListQueryRequest):
    """查询历史列表查询请求"""

    user_id: ObjectUUID | None = Field(default=None, description="用户ID筛选")
    query_type: str | None = Field(default=None, description="查询类型筛选")
    status: Literal["success", "partial", "failed"] | None = Field(default=None, description="状态筛选")
    execution_time_min: float | None = Field(default=None, description="最小执行时间筛选", ge=0)
    execution_time_max: float | None = Field(default=None, description="最大执行时间筛选", ge=0)


class QueryHistoryListResponse(PaginatedResponse[QueryHistoryResponse]):
    """查询历史列表响应"""

    pass


class QueryHistoryCleanupRequest(BaseModel):
    """查询历史清理请求"""

    days_to_keep: int = Field(description="保留天数", ge=1, le=365)
    query_types: list[str] | None = Field(default=None, description="清理的查询类型列表")


class QueryHistoryCleanupResponse(BaseModel):
    """查询历史清理响应"""

    code: int = Field(default=200, description="响应代码")
    message: str = Field(default="清理完成", description="响应消息")
    deleted_count: int = Field(description="删除记录数")


class UserQueryStatistics(BaseModel):
    """用户查询统计"""

    user_id: ObjectUUID = Field(description="用户ID")
    username: str = Field(description="用户名")
    total_queries: int = Field(description="总查询次数")
    success_queries: int = Field(description="成功查询次数")
    failed_queries: int = Field(description="失败查询次数")
    avg_execution_time: float = Field(description="平均执行时间(秒)")
    last_query_time: datetime | None = Field(default=None, description="最后查询时间")


class QueryTypeStatistics(BaseModel):
    """查询类型统计"""

    query_type: str = Field(description="查询类型")
    total_count: int = Field(description="总次数")
    success_count: int = Field(description="成功次数")
    failed_count: int = Field(description="失败次数")
    avg_execution_time: float = Field(description="平均执行时间(秒)")


class QueryHistoryStatisticsRequest(BaseModel):
    """查询历史统计请求"""

    start_date: datetime | None = Field(default=None, description="开始时间")
    end_date: datetime | None = Field(default=None, description="结束时间")
    user_id: ObjectUUID | None = Field(default=None, description="用户ID筛选")
    query_type: str | None = Field(default=None, description="查询类型筛选")


class QueryHistoryStatisticsResponse(StatisticsResponse):
    """查询历史统计响应"""

    pass
