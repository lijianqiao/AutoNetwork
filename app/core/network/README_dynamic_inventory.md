# Nornir动态设备清单模块

## 概述

本模块提供了从数据库动态构建Nornir设备清单的功能，替代传统的静态配置文件方式。支持多厂商设备、认证集成、缓存机制等特性。

## 模块结构

```
app/core/network/
├── dynamic_inventory.py      # 核心动态清单构建器
├── inventory_factory.py      # 工厂类和缓存管理
├── inventory_example.py      # 使用示例
├── test_dynamic_inventory.py # 单元测试
└── README_dynamic_inventory.md # 本文档
```

## 核心功能

### 1. 动态设备清单构建
- 从数据库获取设备信息
- 支持多种过滤条件（厂商、区域、设备类型等）
- 自动构建Host和Group对象
- 集成认证服务

### 2. 工厂模式接口
- 提供便捷的静态方法
- 自动管理数据库连接
- 支持缓存机制

### 3. 缓存管理
- 减少数据库查询
- 可配置缓存生存时间
- 提供缓存统计信息

## 快速开始

### 基础使用

```python
from app.core.network.inventory_factory import InventoryFactory

# 构建所有设备的清单
inventory = await InventoryFactory.build_inventory()
print(f"设备数量: {len(inventory.hosts)}")

# 获取单个设备
device = await InventoryFactory.get_device("SW-CD-01")
if device:
    print(f"设备IP: {device.hostname}")
```

### 过滤设备

```python
# 按厂商过滤
h3c_devices = await InventoryFactory.get_devices_by_vendor("H3C")

# 按区域过滤
chengdu_devices = await InventoryFactory.get_devices_by_region("成都")

# 按设备类型过滤
switches = await InventoryFactory.get_devices_by_type("switch")

# 组合过滤
inventory = await InventoryFactory.build_inventory(
    vendor_ids=[1, 2],  # H3C和华为
    region_ids=[1],     # 成都区域
    device_types=["switch", "router"]
)
```

### 带认证信息的设备清单

```python
# 为特定用户构建带认证信息的清单
inventory = await InventoryFactory.build_inventory(
    device_hostnames=["SW-CD-01", "SW-CD-02"],
    user_id=1  # 用户ID
)
```

### 使用缓存

```python
from app.core.network.inventory_factory import inventory_cache

# 使用缓存获取设备清单
inventory = await inventory_cache.get_inventory(
    device_hostnames=["SW-CD-01"]
)

# 获取缓存统计
stats = inventory_cache.get_cache_stats()
print(f"缓存条目: {stats['total_entries']}")

# 清空缓存
inventory_cache.clear_cache()
```

## 高级用法

### 直接使用构建器

```python
from app.core.network.inventory_factory import InventoryFactory

# 使用上下文管理器
async with InventoryFactory.create_builder() as builder:
    # 构建设备清单
    inventory = await builder.build_inventory(
        device_hostnames=["SW-CD-01", "SW-CD-02"]
    )
    
    # 获取单个设备
    device = await builder.get_device_by_hostname("SW-CD-01")
    
    # 按厂商获取设备
    h3c_devices = await builder.get_devices_by_vendor("H3C")
```

### 设备验证

```python
# 验证设备是否存在
result = await InventoryFactory.validate_devices([
    "SW-CD-01", "SW-CD-02", "SW-CD-99"
])
# 结果: {"SW-CD-01": True, "SW-CD-02": True, "SW-CD-99": False}
```

### 组操作

```python
# 获取设备所属组
groups = await InventoryFactory.get_device_groups("SW-CD-01")
# 结果: ["vendor_h3c", "region_成都", "type_switch"]

# 根据组过滤设备
devices = await InventoryFactory.filter_devices_by_groups([
    "vendor_h3c", "type_switch"
])
```

### 统计信息

```python
# 获取设备清单统计
stats = await InventoryFactory.get_inventory_stats()
print(f"总设备数: {stats['total_devices']}")
print(f"厂商分布: {stats['vendor_distribution']}")
print(f"区域分布: {stats['region_distribution']}")
print(f"类型分布: {stats['type_distribution']}")
```

## 与Nornir集成

### 基本集成

```python
from nornir import InitNornir
from nornir_scrapli.tasks import send_command

# 构建动态设备清单
inventory = await InventoryFactory.build_inventory(
    device_hostnames=["SW-CD-01", "SW-CD-02"],
    user_id=1
)

# 创建Nornir实例（需要额外配置）
# 注意：这里需要根据实际情况调整配置
config = {
    "inventory": {
        "plugin": "DictInventory",
        "options": {
            "hosts": {name: host.dict() for name, host in inventory.hosts.items()},
            "groups": {name: group.dict() for name, group in inventory.groups.items()}
        }
    },
    "runner": {
        "plugin": "threaded",
        "options": {"num_workers": 10}
    }
}

# 执行任务
# nr = InitNornir(config=config)
# result = nr.run(task=send_command, command="display version")
```

## 数据模型

### Host对象数据结构

```python
{
    "name": "SW-CD-01",           # 设备主机名
    "hostname": "192.168.1.10",   # 设备IP地址
    "platform": "hp_comware",     # 设备平台
    "port": 22,                   # SSH端口
    "groups": [                   # 所属组
        "vendor_h3c",
        "region_成都",
        "type_switch"
    ],
    "data": {                     # 设备数据
        "device_id": 1,
        "device_type": "switch",
        "vendor_id": 1,
        "vendor_name": "H3C",
        "vendor_platform": "hp_comware",
        "region_id": 1,
        "region_name": "成都",
        "location": "成都机房A",
        "description": "核心交换机",
        "snmp_community": "oppein@11",
        "is_dynamic_password": True
    },
    "connection_options": {       # 连接选项
        "scrapli": {
            "username": "admin",
            "password": "password123",
            "extras": {
                "ssh_config_file": False,
                "auth_strict_key": False
            }
        },
        "snmp": {
            "extras": {
                "community": "oppein@11",
                "version": "2c"
            }
        }
    }
}
```

### Group对象数据结构

```python
# 厂商组
{
    "name": "vendor_h3c",
    "data": {
        "vendor_id": 1,
        "vendor_name": "H3C",
        "platform": "hp_comware",
        "description": "H3C 厂商设备组"
    }
}

# 区域组
{
    "name": "region_成都",
    "data": {
        "region_id": 1,
        "region_name": "成都",
        "description": "成都 区域设备组"
    }
}

# 设备类型组
{
    "name": "type_switch",
    "data": {
        "device_type": "switch",
        "description": "SWITCH 设备类型组"
    }
}
```

## 配置说明

### 厂商平台映射

| 厂商   | 平台标识    | 说明     |
| ------ | ----------- | -------- |
| H3C    | hp_comware  | 华三设备 |
| Huawei | huawei_vrp  | 华为设备 |
| Cisco  | cisco_iosxe | 思科设备 |

### 认证方式

- **动态密码**: `is_dynamic_password=True`，需要用户手动输入
- **静态密码**: `is_dynamic_password=False`，从数据库获取
- **SNMP社区字符串**: 按基地统一配置

## 性能优化

### 缓存策略

```python
# 配置缓存生存时间（秒）
cache = InventoryCache(cache_ttl=300)  # 5分钟

# 禁用缓存
inventory = await cache.get_inventory(
    device_hostnames=["SW-CD-01"],
    use_cache=False
)
```

### 批量操作

```python
# 一次性获取多个设备，而不是逐个获取
devices = ["SW-CD-01", "SW-CD-02", "SW-CD-03"]
inventory = await InventoryFactory.build_inventory(
    device_hostnames=devices
)

# 而不是
# for device in devices:
#     host = await InventoryFactory.get_device(device)
```

## 错误处理

```python
try:
    inventory = await InventoryFactory.build_inventory()
except Exception as e:
    logger.error(f"构建设备清单失败: {str(e)}")
    # 处理错误
```

## 测试

```bash
# 运行单元测试
python -m pytest app/core/network/test_dynamic_inventory.py -v

# 运行示例
python app/core/network/inventory_example.py
```

## 注意事项

1. **数据库连接**: 模块会自动管理数据库连接，无需手动处理
2. **认证信息**: 包含敏感信息时要注意安全性
3. **缓存管理**: 设备信息变更后需要清空相关缓存
4. **性能考虑**: 大量设备时建议使用过滤条件和缓存
5. **错误处理**: 设备不存在或配置错误时会跳过该设备

## 扩展开发

### 添加新的过滤条件

```python
# 在DynamicInventoryBuilder中添加新的过滤方法
async def get_devices_by_custom_filter(self, custom_field: str) -> List[Host]:
    # 实现自定义过滤逻辑
    pass
```

### 自定义连接选项

```python
# 在_build_connection_options方法中添加新的连接类型
def _build_connection_options(self, device, vendor, auth_info):
    connection_options = {}
    
    # 添加自定义连接选项
    if device.custom_protocol:
        connection_options["custom"] = ConnectionOptions(
            # 自定义配置
        )
    
    return connection_options
```

## 相关文档

- [Nornir官方文档](https://nornir.readthedocs.io/)
- [Scrapli文档](https://carlmontanari.github.io/scrapli/)
- [网络自动化平台设计方案](../../../docs/网络自动化平台设计方案.md)