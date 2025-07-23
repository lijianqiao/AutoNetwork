"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: vendor.py
@DateTime: 2025/07/23
@Docs: 设备厂商模型
"""

from tortoise import fields

from app.models.base import BaseModel


class Vendor(BaseModel):
    """
    设备厂商信息
    """

    vendor_code = fields.CharField(max_length=50, unique=True, description="厂商代码 (h3c, huawei, cisco)")
    vendor_name = fields.CharField(max_length=100, description="厂商名称 (华三、华为、思科)")
    scrapli_platform = fields.CharField(
        max_length=100, description="Scrapli平台标识 (hp_comware, huawei_vrp, cisco_iosxe)"
    )
    default_ssh_port = fields.IntField(default=22, description="默认SSH端口")
    connection_timeout = fields.IntField(default=30, description="连接超时(秒)")
    command_timeout = fields.IntField(default=10, description="命令超时(秒)")

    class Meta(BaseModel.Meta):
        table = "vendors"
        table_description = "厂商表"
        indexes = [
            ("vendor_code",),
            ("vendor_name",),
        ]

    def __str__(self) -> str:
        return self.vendor_name
