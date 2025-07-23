"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: vendor_command.py
@DateTime: 2025/07/23
@Docs: 厂商特定命令模型
"""

from tortoise import fields

from app.models.base import BaseModel


class VendorCommand(BaseModel):
    """
    厂商特定命令 - 解决不同品牌命令差异
    """

    template = fields.ForeignKeyField(
        "models.QueryTemplate", related_name="vendor_commands", description="关联查询模板"
    )
    vendor = fields.ForeignKeyField("models.Vendor", related_name="vendor_commands", description="关联厂商")
    commands = fields.JSONField(description="命令列表 (JSON)")
    parser_type = fields.CharField(max_length=50, description="解析器类型 (textfsm, regex, raw)")
    parser_template = fields.TextField(description="解析模板内容")

    class Meta:  # type: ignore
        table = "vendor_commands"
        table_description = "厂商命令表"
        indexes = [
            ("template_id",),
            ("vendor_id",),
            ("template_id", "vendor_id"),
        ]

    def __str__(self) -> str:
        return f"VendorCommand(template_id={self.template.id}, vendor_id={self.vendor.id})"
