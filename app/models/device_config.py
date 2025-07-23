"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: device_config.py
@DateTime: 2025/07/23
@Docs: 设备配置快照模型
"""

from tortoise import fields

from app.models.base import BaseModel


class DeviceConfig(BaseModel):
    """
    设备配置快照 - 用于配置管理
    """

    device = fields.ForeignKeyField("models.Device", related_name="configs", description="关联设备")
    config_type = fields.CharField(max_length=20, description="配置类型 (running, startup)")
    config_content = fields.TextField(description="配置内容 (压缩存储)")
    config_hash = fields.CharField(max_length=64, description="配置哈希值 (用于快速对比)")
    backup_by = fields.ForeignKeyField(
        "models.User", related_name="device_configs", on_delete=fields.SET_NULL, null=True, description="备份人"
    )
    backup_reason = fields.TextField(null=True, description="备份原因")

    class Meta(BaseModel.Meta):
        table = "device_configs"
        table_description = "设备配置快照表"
        indexes = [
            ("device_id",),
            ("backup_by_id",),
            ("created_at",),
        ]

    def __str__(self) -> str:
        did = getattr(self, "device_id", None)
        return f"DeviceConfig(device_id={did}, hash={self.config_hash})"
