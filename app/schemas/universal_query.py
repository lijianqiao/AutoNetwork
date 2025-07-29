"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: universal_query.py
@DateTime: 2025/01/29
@Docs: 通用查询相关的Pydantic模型
"""

from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class TemplateQueryRequest(BaseModel):
    """基于模板的查询请求"""
    
    template_id: UUID = Field(description="查询模板ID")
    device_ids: list[UUID] = Field(description="目标设备ID列表", min_length=1)
    query_params: dict[str, Any] | None = Field(default=None, description="查询参数（用于命令模板填充）")
    template_version: int | None = Field(default=None, description="指定模板版本（None为最新版本）")
    enable_parsing: bool = Field(default=True, description="是否启用结果解析")
    custom_template: str | None = Field(default=None, description="自定义TextFSM模板名称")


class TemplateTypeQueryRequest(BaseModel):
    """基于模板类型的查询请求"""
    
    template_type: str = Field(description="模板类型 (mac_query, interface_status, config_show)")
    device_ids: list[UUID] = Field(description="目标设备ID列表", min_length=1)
    query_params: dict[str, Any] | None = Field(default=None, description="查询参数")
    enable_parsing: bool = Field(default=True, description="是否启用结果解析")


class TemplateCommandsPreviewRequest(BaseModel):
    """模板命令预览请求"""
    
    template_id: UUID = Field(description="查询模板ID")
    query_params: dict[str, Any] | None = Field(default=None, description="查询参数（用于命令模板填充）")


class TemplateParametersValidationRequest(BaseModel):
    """模板参数验证请求"""
    
    template_id: UUID = Field(description="查询模板ID")
    query_params: dict[str, Any] = Field(description="要验证的查询参数")


class MacQueryRequest(BaseModel):
    """MAC地址查询请求"""
    
    device_ids: list[UUID] = Field(description="目标设备ID列表", min_length=1)
    mac_address: str = Field(description="MAC地址", min_length=1)


class InterfaceStatusQueryRequest(BaseModel):
    """接口状态查询请求"""
    
    device_ids: list[UUID] = Field(description="目标设备ID列表", min_length=1)
    interface_pattern: str | None = Field(default=None, description="接口模式（可选）")


class ConfigShowQueryRequest(BaseModel):
    """配置显示查询请求"""
    
    device_ids: list[UUID] = Field(description="目标设备ID列表", min_length=1)
    config_section: str | None = Field(default=None, description="配置节（可选）")