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
    CONNECT_TIMEOUT: int = Field(default=8, ge=3, le=30)  # 增加到8秒，适应网络延迟

    # 命令执行超时时间（秒）- 优化：平衡速度和可靠性
    COMMAND_TIMEOUT: int = Field(default=15, ge=5, le=120)  # 增加到15秒，避免复杂命令超时

    # 连接重试次数 - 优化：适度重试，提高成功率
    MAX_RETRY_ATTEMPTS: int = Field(default=2, ge=1, le=5)  # 增加到2次，提高成功率

    # 重试间隔时间（秒）- 优化：指数退避策略
    RETRY_INTERVAL: int = Field(default=2, ge=1, le=10)  # 增加到2秒
    ENABLE_EXPONENTIAL_BACKOFF: bool = Field(default=True)  # 启用指数退避
    BACKOFF_MULTIPLIER: float = Field(default=1.5, ge=1.0, le=3.0)  # 退避倍数

    # 连接保活配置 - 新增：保持连接活跃
    ENABLE_KEEPALIVE: bool = Field(default=True)  # 启用保活
    KEEPALIVE_INTERVAL: int = Field(default=30, ge=10, le=300)  # 保活间隔
    KEEPALIVE_COUNT: int = Field(default=3, ge=1, le=10)  # 保活次数

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
    """连接池配置 - 优化后的高性能配置"""

    # 连接池大小 - 优化：动态调整，支持高并发
    MAX_POOL_SIZE: int = Field(default=200, ge=50, le=500)  # 增加到200，支持更高并发
    MIN_POOL_SIZE: int = Field(default=10, ge=5, le=50)  # 增加到10，保持基础连接

    # 连接生命周期（秒）- 优化：平衡性能和资源占用
    MAX_CONNECTION_LIFETIME: int = Field(default=3600, ge=1800, le=14400)  # 1小时，减少频繁重建

    # 空闲连接超时时间（秒）- 优化：快速释放空闲资源
    IDLE_CONNECTION_TIMEOUT: int = Field(default=300, ge=60, le=1800)  # 5分钟，快速回收

    # 连接健康检查间隔（秒）- 优化：平衡检查频率和性能
    HEALTH_CHECK_INTERVAL: int = Field(default=120, ge=60, le=600)  # 2分钟，适中频率

    # 连接获取超时时间（秒）- 优化：快速响应，避免长时间等待
    CONNECTION_ACQUIRE_TIMEOUT: int = Field(default=10, ge=5, le=30)  # 10秒，快速超时

    # 空闲连接清理间隔（秒）- 优化：频繁清理，保持池的健康
    CLEANUP_INTERVAL: int = Field(default=180, ge=60, le=600)  # 3分钟，频繁清理

    # 连接预热配置 - 新增：启动时预创建连接
    ENABLE_CONNECTION_WARMUP: bool = Field(default=True)  # 启用连接预热
    WARMUP_CONNECTION_COUNT: int = Field(default=5, ge=1, le=20)  # 预热连接数

    # 连接池监控配置 - 新增：增强监控能力
    ENABLE_POOL_METRICS: bool = Field(default=True)  # 启用池指标监控
    METRICS_COLLECTION_INTERVAL: int = Field(default=30, ge=10, le=300)  # 指标收集间隔

    # 连接稳定性测试参数 - 优化：更高效的测试策略
    STABILITY_TEST_DURATION: int = Field(default=60, ge=30, le=300)  # 1分钟，更全面测试
    STABILITY_TEST_INTERVAL: int = Field(default=5, ge=2, le=30)  # 5秒，适中间隔
    STABILITY_TEST_COMMAND: str = Field(default="show clock")  # 通用性更好的命令

    # 连接重用配置 - 新增：优化连接重用策略
    ENABLE_CONNECTION_REUSE: bool = Field(default=True)  # 启用连接重用
    MAX_REUSE_COUNT: int = Field(default=100, ge=10, le=1000)  # 最大重用次数

    # 负载均衡配置 - 新增：连接负载均衡
    ENABLE_LOAD_BALANCING: bool = Field(default=True)  # 启用负载均衡
    LOAD_BALANCE_STRATEGY: str = Field(default="round_robin")  # 负载均衡策略


class AuthenticationConfig(BaseModel):
    """认证配置"""

    # 动态密码缓存时间（秒）
    DYNAMIC_PASSWORD_CACHE_TTL: int = Field(default=3600, ge=300, le=86400)  # 1小时

    # 最大缓存密码数量
    MAX_CACHED_PASSWORDS: int = Field(default=1000, ge=100, le=10000)

    # 认证重试次数
    AUTH_MAX_RETRY_ATTEMPTS: int = Field(default=1, ge=1, le=5)

    # 认证超时时间（秒）
    AUTH_TIMEOUT: int = Field(default=15, ge=10, le=120)

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
    """并发控制配置 - 优化后的高并发配置"""

    # 最大并发连接数 - 优化：支持更高并发，配合连接池扩容
    MAX_CONCURRENT_CONNECTIONS: int = Field(default=150, ge=20, le=300)

    # 最大并发查询数 - 优化：提高查询并发度
    MAX_CONCURRENT_QUERIES: int = Field(default=80, ge=10, le=150)

    # 最大并发认证测试数 - 优化：提高认证测试并发度
    MAX_CONCURRENT_AUTH_TESTS: int = Field(default=50, ge=5, le=100)

    # 连接信号量超时时间（秒）- 优化：快速超时，避免阻塞
    SEMAPHORE_TIMEOUT: int = Field(default=20, ge=5, le=120)

    # 批量操作的默认批次大小 - 优化：增加批次大小，提高吞吐量
    DEFAULT_BATCH_SIZE: int = Field(default=30, ge=5, le=100)

    # 动态并发控制 - 新增：根据系统负载动态调整
    ENABLE_DYNAMIC_CONCURRENCY: bool = Field(default=True)  # 启用动态并发控制
    MIN_CONCURRENT_CONNECTIONS: int = Field(default=10, ge=1, le=50)  # 最小并发数
    CONCURRENCY_SCALE_FACTOR: float = Field(default=1.5, ge=1.0, le=3.0)  # 并发扩展因子

    # 队列配置 - 新增：任务队列优化
    MAX_QUEUE_SIZE: int = Field(default=1000, ge=100, le=5000)  # 最大队列大小
    QUEUE_TIMEOUT: int = Field(default=60, ge=10, le=300)  # 队列超时时间


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
