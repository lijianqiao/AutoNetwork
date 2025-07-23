"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: query_history.py
@DateTime: 2025/07/23
@Docs: 查询历史模型
"""

from tortoise import fields

from app.models.base import BaseModel


class QueryHistory(BaseModel):
    """
    查询历史记录 - 仅记录元数据，不存储查询结果
    """

    user = fields.ForeignKeyField(
        "models.User", related_name="query_histories", on_delete=fields.CASCADE, description="查询用户"
    )
    query_type = fields.CharField(max_length=50, description="查询类型")
    query_params = fields.JSONField(description="查询参数 (JSON)")
    target_devices = fields.JSONField(description="目标设备IP列表 (JSON)")
    execution_time = fields.FloatField(description="执行耗时(秒)")
    status = fields.CharField(max_length=20, description="状态 (success, partial, failed)")
    error_message = fields.TextField(null=True, description="错误信息")

    class Meta(BaseModel.Meta):
        table = "query_histories"
        table_description = "查询历史表"
        indexes = [
            ("user_id",),
            ("query_type",),
            ("status",),
            ("created_at",),
        ]

    def __str__(self) -> str:
        return f"QueryHistory(user_id={self.user.id}, type={self.query_type})"
