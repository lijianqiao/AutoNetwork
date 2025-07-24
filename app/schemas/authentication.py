"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: authentication.py
@DateTime: 2025/07/23
@Docs: 设备认证相关的Pydantic模型
"""

from pydantic import BaseModel, Field

from app.schemas.base import BaseResponse
from app.schemas.types import ObjectUUID


class DeviceCredentialsRequest(BaseModel):
    """设备认证凭据请求"""

    device_id: ObjectUUID = Field(description="设备ID")
    dynamic_password: str | None = Field(default=None, description="动态密码（用户手动输入）")


class DeviceCredentialsResponse(BaseModel):
    """设备认证凭据响应"""

    device_id: str = Field(description="设备ID")
    hostname: str = Field(description="设备主机名")
    ip_address: str = Field(description="设备IP地址")
    auth_type: str = Field(description="认证类型 (dynamic/static)")
    username: str = Field(description="用户名")
    has_password: bool = Field(description="是否有密码")
    has_snmp_community: bool = Field(description="是否有SNMP社区字符串")
    ssh_port: int = Field(description="SSH端口")
    region_code: str = Field(description="基地代码")
    vendor_code: str = Field(description="厂商代码")
    scrapli_platform: str = Field(description="Scrapli平台标识")


class AuthenticationTestRequest(BaseModel):
    """认证测试请求"""

    device_id: ObjectUUID = Field(description="设备ID")
    dynamic_password: str | None = Field(default=None, description="动态密码（用户手动输入）")


class AuthenticationTestResult(BaseModel):
    """认证测试结果"""

    success: bool = Field(description="测试是否成功")
    device_id: str = Field(description="设备ID")
    hostname: str | None = Field(default=None, description="设备主机名")
    ip_address: str | None = Field(default=None, description="设备IP地址")
    auth_type: str | None = Field(default=None, description="认证类型")
    username: str | None = Field(default=None, description="用户名")
    has_password: bool | None = Field(default=None, description="是否有密码")
    has_snmp_community: bool | None = Field(default=None, description="是否有SNMP社区字符串")
    ssh_port: int | None = Field(default=None, description="SSH端口")
    credentials_valid: bool | None = Field(default=None, description="凭据是否有效")
    region_code: str | None = Field(default=None, description="基地代码")
    vendor_code: str | None = Field(default=None, description="厂商代码")
    scrapli_platform: str | None = Field(default=None, description="Scrapli平台标识")
    error: str | None = Field(default=None, description="错误信息")
    message: str = Field(description="测试结果消息")


class AuthenticationTestResponse(BaseResponse[AuthenticationTestResult]):
    """认证测试响应"""

    pass


class DynamicPasswordClearRequest(BaseModel):
    """清除动态密码缓存请求"""

    device_id: ObjectUUID | None = Field(default=None, description="设备ID，为空则清除所有缓存")


class DynamicPasswordCacheInfo(BaseModel):
    """动态密码缓存信息"""

    cached_count: int = Field(description="缓存的密码数量")
    message: str = Field(description="缓存状态信息")


class DynamicPasswordCacheResponse(BaseResponse[DynamicPasswordCacheInfo]):
    """动态密码缓存响应"""

    pass


class BatchAuthenticationTestRequest(BaseModel):
    """批量认证测试请求"""

    device_ids: list[ObjectUUID] = Field(description="设备ID列表")
    dynamic_passwords: dict[str, str] | None = Field(
        default=None, description="动态密码映射，key为device_id字符串，value为密码"
    )


class BatchAuthenticationTestResult(BaseModel):
    """批量认证测试结果"""

    total_count: int = Field(description="总测试数量")
    success_count: int = Field(description="成功数量")
    failed_count: int = Field(description="失败数量")
    results: list[AuthenticationTestResult] = Field(description="详细测试结果")
    summary: str = Field(description="测试摘要")


class BatchAuthenticationTestResponse(BaseResponse[BatchAuthenticationTestResult]):
    """批量认证测试响应"""

    pass


class UsernameGenerationRequest(BaseModel):
    """用户名生成请求"""

    network_layer: str = Field(description="网络层级 (access/aggregation/core)")
    region_code: str = Field(description="基地代码")


class UsernameGenerationResult(BaseModel):
    """用户名生成结果"""

    network_layer: str = Field(description="网络层级")
    region_code: str = Field(description="基地代码")
    generated_username: str = Field(description="生成的用户名")
    pattern_used: str = Field(description="使用的模式")


class UsernameGenerationResponse(BaseResponse[UsernameGenerationResult]):
    """用户名生成响应"""

    pass


class AuthenticationConfigInfo(BaseModel):
    """认证配置信息"""

    username_patterns: dict[str, str] = Field(description="用户名生成模式")
    supported_auth_types: list[str] = Field(description="支持的认证类型")
    dynamic_password_cache_enabled: bool = Field(description="是否启用动态密码缓存")
    current_cached_count: int = Field(description="当前缓存的密码数量")


class AuthenticationConfigResponse(BaseResponse[AuthenticationConfigInfo]):
    """认证配置响应"""

    pass
