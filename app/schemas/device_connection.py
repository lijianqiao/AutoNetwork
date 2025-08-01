"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: device_connection.py
@DateTime: 2025/08/01
@Docs: 设备连接与认证相关Schema定义
"""

from uuid import UUID

from pydantic import BaseModel, Field


class DeviceConnectionTestRequest(BaseModel):
    """设备连接测试请求"""

    device_id: UUID = Field(..., description="设备ID")
    dynamic_password: str | None = Field(None, description="动态密码")


class BatchConnectionTestRequest(BaseModel):
    """批量设备连接测试请求"""

    device_ids: list[UUID] = Field(..., description="设备ID列表")
    dynamic_password: str | None = Field(None, description="统一动态密码（适用于所有动态密码设备）")
    dynamic_passwords: dict[str, str] | None = Field(None, description="设备特定动态密码映射（优先级高于统一密码）")
    max_concurrent: int = Field(20, ge=1, le=50, description="最大并发数")


class ConnectionStabilityTestRequest(BaseModel):
    """连接稳定性测试请求"""

    device_id: UUID = Field(..., description="设备ID")
    duration: int = Field(60, ge=10, le=3600, description="测试持续时间（秒）")
    interval: int = Field(10, ge=5, le=60, description="测试间隔（秒）")


class CredentialsValidationRequest(BaseModel):
    """认证凭据验证请求"""

    device_id: UUID = Field(..., description="设备ID")
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")
    ssh_port: int = Field(22, ge=1, le=65535, description="SSH端口")


class PasswordEncryptionRequest(BaseModel):
    """密码加密请求"""

    password: str = Field(..., description="明文密码")


class DevicesByCriteriaTestRequest(BaseModel):
    """根据条件批量测试设备请求"""

    vendor_id: UUID | None = Field(None, description="厂商ID")
    region_id: UUID | None = Field(None, description="基地ID")
    device_type: str | None = Field(None, description="设备类型")
    network_layer: str | None = Field(None, description="网络层级")
    is_active: bool = Field(True, description="是否活跃")
    max_concurrent: int = Field(20, ge=1, le=50, description="最大并发数")


class DeviceConnectionTestResponse(BaseModel):
    """设备连接测试响应"""

    device_id: UUID = Field(..., description="设备ID")
    success: bool = Field(..., description="连接是否成功")
    message: str = Field(..., description="连接结果消息")
    response_time: float | None = Field(None, description="响应时间（毫秒）")
    error_details: str | None = Field(None, description="错误详情")


class BatchConnectionTestResponse(BaseModel):
    """批量连接测试响应"""

    total_devices: int = Field(..., description="测试设备总数")
    successful_devices: int = Field(..., description="成功连接设备数")
    failed_devices: int = Field(..., description="连接失败设备数")
    results: list[DeviceConnectionTestResponse] = Field(..., description="详细测试结果")
    execution_time: float = Field(..., description="总执行时间（秒）")


class ConnectionStabilityTestResponse(BaseModel):
    """连接稳定性测试响应"""

    device_id: UUID = Field(..., description="设备ID")
    total_tests: int = Field(..., description="总测试次数")
    successful_tests: int = Field(..., description="成功测试次数")
    failed_tests: int = Field(..., description="失败测试次数")
    success_rate: float = Field(..., description="成功率")
    average_response_time: float = Field(..., description="平均响应时间（毫秒）")
    test_results: list[dict] = Field(..., description="详细测试结果")


class CredentialsValidationResponse(BaseModel):
    """认证凭据验证响应"""

    device_id: UUID = Field(..., description="设备ID")
    valid: bool = Field(..., description="凭据是否有效")
    message: str = Field(..., description="验证结果消息")
    authentication_time: float | None = Field(None, description="认证时间（毫秒）")


class PasswordEncryptionResponse(BaseModel):
    """密码加密响应"""

    encrypted_password: str = Field(..., description="加密后的密码")
    encryption_method: str = Field(..., description="加密方法")


class DevicesByCriteriaTestResponse(BaseModel):
    """根据条件批量测试设备响应"""

    matched_devices: int = Field(..., description="匹配的设备数量")
    tested_devices: int = Field(..., description="测试的设备数量")
    successful_devices: int = Field(..., description="成功连接设备数")
    failed_devices: int = Field(..., description="连接失败设备数")
    results: list[DeviceConnectionTestResponse] = Field(..., description="详细测试结果")
    execution_time: float = Field(..., description="总执行时间（秒）")
