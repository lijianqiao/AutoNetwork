"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: config.py
@DateTime: 2025/07/25 21:06:16
@Docs: 网络连接管理配置 - 定义设备连接、连接池、认证等相关配置参数
"""

from pydantic import BaseModel, Field


class ScrapliPlatformConfig(BaseModel):
    """Scrapli平台配置"""

    # 厂商代码到Scrapli平台的映射
    VENDOR_PLATFORM_MAPPING: dict[str, str] = {
        "cisco": "cisco_iosxe",
        "huawei": "huawei_vrp",
        "h3c": "hp_comware",
        "juniper": "juniper_junos",
        "arista": "arista_eos",
        "nokia": "nokia_sros",
        "fortinet": "fortinet_fortios",
        "paloalto": "paloalto_panos",
        "checkpoint": "checkpoint_gaia",
        "f5": "f5_tmsh",
        "dell": "dell_os10",
        "hp": "hp_procurve",
        "extreme": "extreme_exos",
        "mikrotik": "mikrotik_routeros",
        "vyos": "vyos",
        "linux": "linux",
    }

    # 默认平台（当无法识别厂商时使用）
    DEFAULT_PLATFORM: str = "generic"

    # 平台特定的默认端口
    PLATFORM_DEFAULT_PORTS: dict[str, int] = {
        "cisco_iosxe": 22,
        "huawei_vrp": 22,
        "hp_comware": 22,
        "juniper_junos": 22,
        "arista_eos": 22,
        "nokia_sros": 22,
        "fortinet_fortios": 22,
        "paloalto_panos": 22,
        "checkpoint_gaia": 22,
        "f5_tmsh": 22,
        "dell_os10": 22,
        "hp_procurve": 22,
        "extreme_exos": 22,
        "mikrotik_routeros": 22,
        "vyos": 22,
        "linux": 22,
        "generic": 22,
    }


class ConnectionConfig(BaseModel):
    """连接配置"""

    # 连接超时时间（秒）
    CONNECT_TIMEOUT: int = Field(default=30, ge=5, le=300)

    # 命令执行超时时间（秒）
    COMMAND_TIMEOUT: int = Field(default=60, ge=10, le=600)

    # 连接重试次数
    MAX_RETRY_ATTEMPTS: int = Field(default=3, ge=1, le=10)

    # 重试间隔时间（秒）
    RETRY_INTERVAL: int = Field(default=5, ge=1, le=60)

    # SSH连接参数
    SSH_CONFIG_FILE: str | bool | None = Field(default=False)

    # 是否启用严格主机密钥检查
    STRICT_HOST_KEY_CHECKING: bool = Field(default=False)

    # 是否启用SSH压缩
    SSH_COMPRESSION: bool = Field(default=False)

    # SSH加密算法偏好
    SSH_ENCRYPTION_ALGORITHMS: list[str] | None = Field(default=None)

    # 终端设置
    TERMINAL_WIDTH: int = Field(default=120, ge=80, le=200)
    TERMINAL_HEIGHT: int = Field(default=24, ge=20, le=50)


class ConnectionPoolConfig(BaseModel):
    """连接池配置"""

    # 连接池大小
    MAX_POOL_SIZE: int = Field(default=100, ge=10, le=1000)
    MIN_POOL_SIZE: int = Field(default=5, ge=1, le=50)

    # 连接生命周期（秒）
    MAX_CONNECTION_LIFETIME: int = Field(default=3600, ge=300, le=86400)  # 1小时

    # 空闲连接超时时间（秒）
    IDLE_CONNECTION_TIMEOUT: int = Field(default=1800, ge=60, le=7200)  # 30分钟

    # 连接健康检查间隔（秒）
    HEALTH_CHECK_INTERVAL: int = Field(default=300, ge=60, le=1800)  # 5分钟

    # 连接获取超时时间（秒）
    CONNECTION_ACQUIRE_TIMEOUT: int = Field(default=30, ge=5, le=120)

    # 空闲连接清理间隔（秒）
    CLEANUP_INTERVAL: int = Field(default=600, ge=60, le=3600)  # 10分钟

    # 连接稳定性测试参数
    STABILITY_TEST_DURATION: int = Field(default=60, ge=10, le=300)  # 1分钟
    STABILITY_TEST_INTERVAL: int = Field(default=5, ge=1, le=30)  # 5秒
    STABILITY_TEST_COMMAND: str = Field(default="display clock")  # 稳定性测试命令


class AuthenticationConfig(BaseModel):
    """认证配置"""

    # 动态密码缓存时间（秒）
    DYNAMIC_PASSWORD_CACHE_TTL: int = Field(default=3600, ge=300, le=86400)  # 1小时

    # 最大缓存密码数量
    MAX_CACHED_PASSWORDS: int = Field(default=1000, ge=100, le=10000)

    # 认证重试次数
    AUTH_MAX_RETRY_ATTEMPTS: int = Field(default=2, ge=1, le=5)

    # 认证超时时间（秒）
    AUTH_TIMEOUT: int = Field(default=30, ge=10, le=120)

    # 用户名生成规则
    USERNAME_PATTERNS: dict[str, str] = {
        "core": "netadmin_{region_code}",
        "aggregation": "netagg_{region_code}",
        "access": "netacc_{region_code}",
        "default": "netuser_{region_code}",
    }

    # 默认用户名（当无法生成动态用户名时使用）
    DEFAULT_USERNAME: str = Field(default="admin")

    # 密码复杂度要求
    PASSWORD_MIN_LENGTH: int = Field(default=8, ge=6, le=32)
    PASSWORD_REQUIRE_SPECIAL_CHARS: bool = Field(default=False)


class ConcurrencyConfig(BaseModel):
    """并发控制配置"""

    # 最大并发连接数
    MAX_CONCURRENT_CONNECTIONS: int = Field(default=50, ge=5, le=200)

    # 最大并发查询数
    MAX_CONCURRENT_QUERIES: int = Field(default=20, ge=5, le=100)

    # 最大并发认证测试数
    MAX_CONCURRENT_AUTH_TESTS: int = Field(default=10, ge=1, le=50)

    # 连接信号量超时时间（秒）
    SEMAPHORE_TIMEOUT: int = Field(default=60, ge=10, le=300)

    # 批量操作的默认批次大小
    DEFAULT_BATCH_SIZE: int = Field(default=10, ge=1, le=50)


class MonitoringConfig(BaseModel):
    """监控配置"""

    # 是否启用性能监控
    ENABLE_PERFORMANCE_MONITORING: bool = Field(default=True)

    # 是否启用连接统计
    ENABLE_CONNECTION_STATS: bool = Field(default=True)

    # 统计信息保留时间（秒）
    STATS_RETENTION_TIME: int = Field(default=86400, ge=3600, le=604800)  # 1天

    # 慢查询阈值（秒）
    SLOW_QUERY_THRESHOLD: float = Field(default=10.0, ge=1.0, le=60.0)

    # 连接失败告警阈值
    CONNECTION_FAILURE_THRESHOLD: int = Field(default=5, ge=1, le=20)

    # 监控数据采集间隔（秒）
    MONITORING_INTERVAL: int = Field(default=60, ge=10, le=300)


class SecurityConfig(BaseModel):
    """安全配置"""

    # 是否启用连接加密
    ENABLE_CONNECTION_ENCRYPTION: bool = Field(default=False)

    # 是否记录敏感信息（密码等）
    LOG_SENSITIVE_INFO: bool = Field(default=False)

    # 连接日志级别
    CONNECTION_LOG_LEVEL: str = Field(default="INFO")

    # 是否启用连接审计
    ENABLE_CONNECTION_AUDIT: bool = Field(default=True)

    # 审计日志保留时间（天）
    AUDIT_LOG_RETENTION_DAYS: int = Field(default=90, ge=7, le=365)

    # 允许的SSH密钥类型
    ALLOWED_SSH_KEY_TYPES: list[str] = Field(default=["rsa", "ecdsa", "ed25519"])

    # 最小SSH密钥长度
    MIN_SSH_KEY_LENGTH: int = Field(default=2048, ge=1024, le=8192)


class NetworkConnectionConfig(BaseModel):
    """网络连接管理总配置"""

    scrapli_platform: ScrapliPlatformConfig = Field(default_factory=ScrapliPlatformConfig)
    connection: ConnectionConfig = Field(default_factory=ConnectionConfig)
    connection_pool: ConnectionPoolConfig = Field(default_factory=ConnectionPoolConfig)
    authentication: AuthenticationConfig = Field(default_factory=AuthenticationConfig)
    concurrency: ConcurrencyConfig = Field(default_factory=ConcurrencyConfig)
    monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)


# 全局配置实例
network_config = NetworkConnectionConfig()


def get_platform_for_vendor(vendor_code: str) -> str:
    """根据厂商代码获取Scrapli平台标识"""
    vendor_code_lower = vendor_code.lower() if vendor_code else ""
    return network_config.scrapli_platform.VENDOR_PLATFORM_MAPPING.get(
        vendor_code_lower, network_config.scrapli_platform.DEFAULT_PLATFORM
    )


def get_default_port_for_platform(platform: str) -> int:
    """根据平台获取默认端口"""
    return network_config.scrapli_platform.PLATFORM_DEFAULT_PORTS.get(platform, 22)


def get_username_pattern(network_layer: str) -> str:
    """根据网络层级获取用户名模式"""
    network_layer_lower = network_layer.lower() if network_layer else "default"
    return network_config.authentication.USERNAME_PATTERNS.get(
        network_layer_lower, network_config.authentication.USERNAME_PATTERNS["default"]
    )
