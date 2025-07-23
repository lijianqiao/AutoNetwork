"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: query_template.py
@DateTime: 2025/07/23
@Docs: 查询模板模型
"""

from tortoise import fields

from app.models.base import BaseModel


class QueryTemplate(BaseModel):
    """
    查询模板 - 支持多厂商命令差异
    """

    template_name = fields.CharField(max_length=100, description="模板名称")
    template_type = fields.CharField(max_length=50, description="模板类型 (mac_query, interface_status, config_show)")
    description = fields.TextField(null=True, description="描述")
    is_active = fields.BooleanField(default=True, description="是否启用")

    class Meta(BaseModel.Meta):
        table = "query_templates"
        table_description = "查询模板表"
        indexes = [
            ("template_type",),
            ("is_active",),
            ("template_name",),
        ]

    def __str__(self) -> str:
        return self.template_name
