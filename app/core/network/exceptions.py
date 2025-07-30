"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: exceptions.py
@DateTime: 2025/07/25
@Docs: 网络模块统一异常处理
"""

from typing import Any

from app.core.exceptions import BusinessException


class NetworkException(BusinessException):
    """网络模块基础异常"""

    def __init__(
        self,
        message: str = "网络操作失败",
        detail: str | dict[str, Any] | None = None,
    ):
        super().__init__(message=message, detail=detail)


class DeviceConnectionException(NetworkException):
    """设备连接异常"""

    def __init__(
        self,
        device_info: str,
        message: str = "设备连接失败",
        detail: str | dict[str, Any] | None = None,
    ):
        self.device_info = device_info
        full_message = f"{message}: {device_info}"
        super().__init__(message=full_message, detail=detail)


class AuthenticationException(NetworkException):
    """设备认证异常"""

    def __init__(
        self,
        device_info: str,
        auth_type: str | None = None,
        message: str = "设备认证失败",
        detail: str | dict[str, Any] | None = None,
    ):
        self.device_info = device_info
        self.auth_type = auth_type
        full_message = f"{message}: {device_info}"
        if auth_type:
            full_message += f" (认证类型: {auth_type})"
        super().__init__(message=full_message, detail=detail)


class CommandExecutionException(NetworkException):
    """命令执行异常"""

    def __init__(
        self,
        device_info: str,
        command: str,
        message: str = "命令执行失败",
        detail: str | dict[str, Any] | None = None,
    ):
        self.device_info = device_info
        self.command = command
        full_message = f"{message}: {device_info}, 命令: {command}"
        super().__init__(message=full_message, detail=detail)


class ConnectionPoolException(NetworkException):
    """连接池异常"""

    def __init__(
        self,
        message: str = "连接池操作失败",
        detail: str | dict[str, Any] | None = None,
    ):
        super().__init__(message=message, detail=detail)


class QueryEngineException(NetworkException):
    """查询引擎异常"""

    def __init__(
        self,
        query_type: str | None = None,
        message: str = "查询引擎操作失败",
        detail: str | dict[str, Any] | None = None,
    ):
        self.query_type = query_type
        full_message = message
        if query_type:
            full_message += f" (查询类型: {query_type})"
        super().__init__(message=full_message, detail=detail)


class ConfigurationException(NetworkException):
    """配置管理异常"""

    def __init__(
        self,
        config_type: str | None = None,
        message: str = "配置管理操作失败",
        detail: str | dict[str, Any] | None = None,
    ):
        self.config_type = config_type
        full_message = message
        if config_type:
            full_message += f" (配置类型: {config_type})"
        super().__init__(message=full_message, detail=detail)


class DynamicPasswordRequiredException(AuthenticationException):
    """动态密码需要输入异常"""

    def __init__(
        self,
        device_info: str,
        device_id: str,
        hostname: str,
        detail: str | dict[str, Any] | None = None,
    ):
        self.device_id = device_id
        self.hostname = hostname

        if detail is None:
            detail = {
                "device_id": device_id,
                "hostname": hostname,
                "auth_type": "dynamic",
                "requires_password_input": True,
            }

        super().__init__(
            device_info=device_info,
            auth_type="dynamic",
            message="设备使用动态密码认证，请提供密码",
            detail=detail,
        )


class CredentialsIncompleteException(AuthenticationException):
    """认证凭据不完整异常"""

    def __init__(
        self,
        device_info: str,
        device_id: str,
        hostname: str,
        missing_username: bool = False,
        missing_password: bool = False,
        detail: str | dict[str, Any] | None = None,
    ):
        self.device_id = device_id
        self.hostname = hostname
        self.missing_username = missing_username
        self.missing_password = missing_password

        if detail is None:
            detail = {
                "device_id": device_id,
                "hostname": hostname,
                "auth_type": "static",
                "missing_username": missing_username,
                "missing_password": missing_password,
            }

        super().__init__(
            device_info=device_info,
            auth_type="static",
            message="设备的静态认证凭据不完整",
            detail=detail,
        )
