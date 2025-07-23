"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: region.py
@DateTime: 2025/07/23
@Docs: 基地模型
"""

from tortoise import fields

from app.models.base import BaseModel


class Region(BaseModel):
    """
    基地信息
    """

    region_code = fields.CharField(max_length=50, unique=True, description="基地代码 (cd, wx, sh)")
    region_name = fields.CharField(max_length=100, description="基地名称 (成都、无锡、上海)")
    snmp_community = fields.CharField(max_length=200, description="SNMP社区字符串 (加密存储)")
    description = fields.TextField(null=True, description="描述")

    class Meta(BaseModel.Meta):
        table = "regions"
        table_description = "基地表"
        indexes = [
            ("region_code",),
            ("region_name",),
        ]

    def __str__(self) -> str:
        return self.region_name
