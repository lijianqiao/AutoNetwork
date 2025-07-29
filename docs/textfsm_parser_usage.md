# TextFSM解析器使用指南

## 概述

TextFSM解析器是AutoNetwork系统中用于标准化和结构化网络设备命令输出的核心组件。它集成了ntc-templates库，支持多种网络设备平台的命令输出解析。

## 主要特性

### 1. 通用解析能力
- 支持20+种网络设备平台（Cisco IOS/XE/NX-OS、华为VRP、华三Comware等）
- 内置921个ntc-templates模板
- 自动模板匹配和模糊查找
- 回退解析机制

### 2. ntc-templates集成
- 直接使用成熟的开源模板库
- 自动模板缓存机制
- 支持标准化命令名称映射

### 3. 自定义模板支持
- 支持上传和管理自定义TextFSM模板
- 模板验证和错误检查
- 优先使用自定义模板

## 核心类和方法

### TextFSMParser类

```python
from app.core.network import TextFSMParser

# 初始化解析器
parser = TextFSMParser()

# 解析命令输出
result = await parser.parse_command_output(
    command_output="show version输出内容",
    platform="cisco_ios",
    command="show version"
)

# 添加自定义模板
await parser.add_custom_template(
    template_name="my_custom_template",
    template_content="TextFSM模板内容",
    description="自定义模板描述"
)

# 获取统计信息
stats = parser.get_stats()
```

### QueryResultParser类

```python
from app.core.network import QueryResultParser

# 初始化查询结果解析器
result_parser = QueryResultParser()

# 解析Nornir查询结果
parsed_results = await result_parser.parse_query_results(
    nornir_results=raw_results,
    commands=["show version", "show interfaces"],
    devices=device_list,
    enable_parsing=True
)

# 解析单个命令输出
single_result = await result_parser.parse_single_command_output(
    command_output="命令输出内容",
    platform="cisco_ios",
    command="show interfaces status"
)
```

### NornirQueryEngine集成

```python
from app.core.network import NornirQueryEngine

# 初始化查询引擎（已集成解析器）
engine = NornirQueryEngine()

# 执行带解析的查询
parsed_results = await engine.execute_parsed_query(
    devices=device_list,
    template_id=template_uuid,
    query_params={"interface": "GigabitEthernet0/1"},
    enable_parsing=True
)

# 解析单个输出
result = await engine.parse_single_output(
    command_output="show version输出",
    platform="cisco_ios",
    command="show version"
)
```

## 支持的平台

### Scrapli平台到TextFSM平台映射

| Scrapli平台      | TextFSM平台      | 说明             |
| ---------------- | ---------------- | ---------------- |
| cisco_iosxe      | cisco_ios        | Cisco IOS-XE     |
| cisco_ios        | cisco_ios        | Cisco IOS        |
| cisco_nxos       | cisco_nxos       | Cisco NX-OS      |
| cisco_xr         | cisco_xr         | Cisco IOS-XR     |
| huawei_vrp       | huawei_vrp       | 华为VRP          |
| hp_comware       | hp_comware       | 华三Comware      |
| juniper_junos    | juniper_junos    | Juniper JunOS    |
| arista_eos       | arista_eos       | Arista EOS       |
| nokia_sros       | nokia_sros       | Nokia SR OS      |
| fortinet_fortios | fortinet_fortios | Fortinet FortiOS |

## 使用示例

### 1. 基本解析示例

```python
import asyncio
from app.core.network import TextFSMParser

async def parse_cisco_version():
    parser = TextFSMParser()
    
    # Cisco IOS show version输出
    output = """
    Cisco IOS Software, C2960X Software (C2960X-UNIVERSALK9-M), Version 15.2(4)E7
    Technical Support: http://www.cisco.com/techsupport
    Copyright (c) 1986-2018 by Cisco Systems, Inc.
    """
    
    result = await parser.parse_command_output(
        command_output=output,
        platform="cisco_ios",
        command="show version"
    )
    
    print(f"解析结果: {result}")
    # 输出: [{'SOFTWARE_IMAGE': 'C2960X-UNIVERSALK9-M', 'VERSION': '15.2(4)E7', ...}]

asyncio.run(parse_cisco_version())
```

### 2. 自定义模板示例

```python
async def add_custom_template():
    parser = TextFSMParser()
    
    # 自定义TextFSM模板
    template_content = """
    Value INTERFACE (\S+)
    Value STATUS (\S+)
    Value PROTOCOL (\S+)
    
    Start
      ^${INTERFACE}\s+${STATUS}\s+${PROTOCOL} -> Record
    """
    
    # 添加自定义模板
    success = await parser.add_custom_template(
        template_name="custom_interface_status",
        template_content=template_content,
        description="自定义接口状态解析模板"
    )
    
    if success:
        print("自定义模板添加成功")
        
        # 使用自定义模板解析
        result = await parser.parse_command_output(
            command_output="Gi0/1 up up\nGi0/2 down down",
            platform="cisco_ios",
            command="show interfaces brief",
            custom_template="custom_interface_status"
        )
        print(f"解析结果: {result}")
```

### 3. 集成查询示例

```python
from app.core.network import NornirQueryEngine
from app.models.device import Device

async def query_with_parsing():
    engine = NornirQueryEngine()
    
    # 假设有设备列表
    devices = [...]  # Device对象列表
    template_id = "..."  # 查询模板UUID
    
    # 执行带解析的查询
    results = await engine.execute_parsed_query(
        devices=devices,
        template_id=template_id,
        enable_parsing=True
    )
    
    for result in results:
        print(f"设备: {result.hostname}")
        print(f"解析成功: {result.parsing_success}")
        if result.parsed_data:
            print(f"结构化数据: {result.parsed_data}")
        else:
            print(f"原始输出: {result.raw_output}")
```

## 错误处理

### 1. 模板未找到
当找不到合适的模板时，解析器会使用回退解析机制，返回简单的行级解析结果。

### 2. 解析失败
当TextFSM解析失败时，会记录错误日志并返回原始输出。

### 3. 自定义模板验证
添加自定义模板时会进行格式验证，确保模板语法正确。

## 性能优化

### 1. 模板缓存
- 自动缓存已加载的模板，避免重复文件读取
- 支持缓存清理和更新

### 2. 异步处理
- 所有解析操作都是异步的，不会阻塞主线程
- 支持并发解析多个命令输出

### 3. 模糊匹配
- 当精确匹配失败时，使用模糊匹配算法查找最佳模板
- 基于命令关键词的智能匹配

## 统计信息

```python
# 获取解析器统计信息
stats = parser.get_stats()
print(f"ntc-templates数量: {stats['ntc_templates_count']}")
print(f"自定义模板数量: {stats['custom_templates_count']}")
print(f"缓存模板数量: {stats['cached_templates_count']}")

# 获取查询结果解析器统计信息
result_stats = await result_parser.get_parser_stats()
print(f"支持的平台数量: {result_stats['supported_platforms']}")
```

## 注意事项

1. **模板命名规范**: 自定义模板名称应该具有描述性，避免与ntc-templates冲突
2. **平台标识**: 确保使用正确的平台标识符，参考支持的平台列表
3. **命令标准化**: 解析器会自动标准化命令名称，移除参数和特殊字符
4. **编码处理**: 所有模板文件使用UTF-8编码
5. **错误日志**: 解析失败时会记录详细的错误日志，便于调试

## 扩展开发

### 添加新平台支持

1. 在`QueryResultParser`中添加平台映射
2. 确保ntc-templates中有对应的模板文件
3. 测试新平台的解析功能

### 自定义解析逻辑

可以继承`TextFSMParser`类，重写特定方法来实现自定义解析逻辑：

```python
class CustomTextFSMParser(TextFSMParser):
    async def _get_template(self, platform: str, command: str, custom_template: str | None = None):
        # 自定义模板获取逻辑
        return await super()._get_template(platform, command, custom_template)
    
    def _fallback_parse(self, command_output: str) -> list[dict[str, Any]]:
        # 自定义回退解析逻辑
        return super()._fallback_parse(command_output)
```