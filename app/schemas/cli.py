"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: cli.py
@DateTime: 2025/07/30 10:28:06
@Docs: 定义与CLI会话相关的Pydantic模型
"""

from typing import Any

from pydantic import Field

from app.schemas.base import BaseModel


class DeviceConnectionConfig(BaseModel):
    """手动设备连接配置"""

    ip_address: str = Field(..., description="设备IP地址")
    username: str = Field(..., description="登录用户名")
    password: str = Field(..., description="登录密码")
    ssh_port: int = Field(default=22, ge=1, le=65535, description="SSH端口")
    platform: str = Field(default="generic", description="设备平台类型")


class SessionInfo(BaseModel):
    """会话信息"""

    session_id: str = Field(..., description="会话ID")
    user_id: str = Field(..., description="用户ID")
    is_connected: bool = Field(..., description="是否已连接")
    created_at: str = Field(..., description="创建时间")
    last_activity: str = Field(..., description="最后活动时间")
    command_count: int = Field(..., description="已执行命令数")
    in_config_mode: bool = Field(..., description="是否在配置模式")
    device_prompt: str = Field(..., description="设备提示符")
    device_info: dict[str, Any] = Field(..., description="设备信息")


class SessionStats(BaseModel):
    """会话统计信息"""

    total_sessions: int = Field(..., description="总会话数")
    connected_sessions: int = Field(..., description="已连接会话数")
    disconnected_sessions: int = Field(..., description="未连接会话数")
    total_commands_executed: int = Field(..., description="总执行命令数")
    user_sessions: dict[str, int] = Field(..., description="用户会话分布")
    avg_commands_per_session: float = Field(..., description="平均每会话命令数")
    timestamp: str = Field(..., description="统计时间")


class PlatformInfo(BaseModel):
    """平台信息"""

    vendor_code: str = Field(..., description="厂商代码")
    vendor_name: str = Field(..., description="厂商名称")
    scrapli_platform: str = Field(..., description="Scrapli平台标识")
    description: str = Field(..., description="描述")


class ValidationResult(BaseModel):
    """验证结果"""

    valid: bool = Field(..., description="是否验证通过")
    message: str | None = Field(None, description="成功消息")
    error: str | None = Field(None, description="错误信息")
