"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: device.py
@DateTime: 2025/07/23
@Docs: 网络设备模型
"""

from tortoise import fields

from app.models.base import BaseModel


class Device(BaseModel):
    """
    网络设备信息
    """

    hostname = fields.CharField(max_length=100, unique=True, description="设备主机名")
    ip_address = fields.CharField(max_length=45, unique=True, description="管理IP地址")
    device_type = fields.CharField(max_length=50, description="设备类型 (switch, router, firewall)")
    network_layer = fields.CharField(max_length=50, description="网络层级 (access, aggregation, core)")

    vendor = fields.ForeignKeyField("models.Vendor", related_name="devices", description="关联厂商")
    region = fields.ForeignKeyField("models.Region", related_name="devices", description="关联基地")

    model = fields.CharField(max_length=100, description="设备型号")
    serial_number = fields.CharField(max_length=100, description="序列号")
    location = fields.CharField(max_length=200, description="物理位置")

    auth_type = fields.CharField(max_length=50, description="认证类型 (dynamic, static)")
    static_username = fields.CharField(max_length=200, null=True, description="静态用户名")
    static_password = fields.CharField(max_length=200, null=True, description="静态密码 (加密存储)")
    ssh_port = fields.IntField(default=22, description="SSH端口")

    is_active = fields.BooleanField(default=True, description="是否在用")
    last_connected_at = fields.DatetimeField(null=True, description="最后连接时间")

    class Meta:  # type: ignore
        table = "devices"
        table_description = "网络设备表"
        indexes = [
            ("hostname",),
            ("ip_address",),
            ("device_type",),
            ("network_layer",),
            ("vendor_id",),
            ("region_id",),
            ("is_active",),
            ("last_connected_at",),
            ("vendor_id", "region_id"),
            ("created_at",),
        ]

    def __str__(self) -> str:
        return self.hostname
