# AutoNetwork API 文档

**版本**: v1  
**基础URL + 版本**: `http://localhost:8000/api/v1`  
**认证方式**: JWT Bearer Token  
**内容类型**: application/json

## 📋 目录

- [1. 认证管理](#1-认证管理)
- [2. 用户管理](#2-用户管理)
- [3. 角色管理](#3-角色管理)
- [4. 权限管理](#4-权限管理)
- [5. 用户关系管理](#5-用户关系管理)
- [6. 设备管理](#6-设备管理)
- [7. 基地管理](#7-基地管理)
- [8. 厂商管理](#8-厂商管理)
- [9. 厂商命令管理](#9-厂商命令管理)
- [10. 设备连接与认证](10-设备连接与认证)
- [11. 网络查询](#11-网络查询)
- [12. 查询模板管理](#12-查询模板管理)
- [13. 查询历史管理](#13-查询历史管理)
- [14. 设备配置管理](#14-设备配置管理)
- [15. 导入导出](#15-导入导出)
- [16. CLI终端](#16-cli终端)
- [17. 操作日志管理](#17-操作日志管理)
- [18. 权限缓存管理](#18-权限缓存管理)
- [19. 系统统计](#19-系统统计)
- [20. 后台管理](#20-后台管理)
- [21. Web页面](#21-web页面)

---

## 1. 认证管理

### 1.1 用户登录

**POST** `/auth/login`

使用用户名密码登录系统。

**请求体**:
```json
{
  "username": "admin",
  "password": "password123"
}
```

**响应**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1Ni...",
  "refresh_token": "eyJhbGciOiJIUzI1Ni...",
  "token_type": "Bearer",
  "expires_in": 604800
}
```

### 1.2 表单登录

**POST** `/auth/login/form`

OAuth2表单登录接口，适用于Swagger UI。

### 1.3 退出登录

**POST** `/auth/logout`

退出当前登录会话。

### 1.4 刷新令牌

**POST** `/auth/refresh`

刷新访问令牌。

**请求**：
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1Ni..."
}
```

**响应**：
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI4ODdhYjkyZC03N2FlLTQwYmYtYTc4Yi1hM2JhZTMwYzlhNWUiLCJ1c2VybmFtZSI6ImFkbWluIiwiaXNfc3VwZXJ1c2VyIjp0cnVlLCJpc19hY3RpdmUiOnRydWUsImV4cCI6MTc1NDY0MTU0MCwidHlwZSI6ImFjY2VzcyJ9.UyJ0ymmndhmnAz_iieTBo47M3J_-OOVZAAoJ1_7viuo",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI4ODdhYjkyZC03N2FlLTQwYmYtYTc4Yi1hM2JhZTMwYzlhNWUiLCJ1c2VybmFtZSI6ImFkbWluIiwiaXNfc3VwZXJ1c2VyIjp0cnVlLCJpc19hY3RpdmUiOnRydWUsImV4cCI6MTc1NDY0MTQ4OCwidHlwZSI6InJlZnJlc2gifQ.YbxgroXyigl6lgKLyJ4Y7F-xkLSV26YI2dSqg3RO1Hw",
  "token_type": "Bearer",
  "expires_in": 604800
}
```

### 1.5 获取用户信息

**GET** `/auth/profile`

获取当前登录用户的个人信息。

### 1.6 更新用户信息

**PUT** `/auth/profile`

更新当前用户的个人信息。

### 1.7 修改密码

**PUT** `/auth/password`

修改当前用户密码。

---

## 2. 用户管理

### 2.1 获取用户列表

**GET** `/users`

获取用户列表，支持分页和过滤。

### 2.2 获取用户详情

**GET** `/users/{user_id}`

获取指定用户的详细信息

### 2.3 创建用户

**POST** `/users`

创建新用户

### 2.4 更新用户

**PUT** `/users/{user_id}`

更新用户信息

### 2.5 删除用户

**DELETE** `/users/{user_id}`

删除指定用户（软删除）

### 2.6 批量操作

**POST** `/users/batch` - 批量创建用户  
**PUT** `/users/batch` - 批量更新用户  
**DELETE** `/users/batch` - 批量删除用户

---

## 3. 角色管理

### 3.1 获取角色列表

**GET** `/roles`

获取角色列表，支持分页和过滤

### 3.2 创建角色

**POST** `/roles`

创建新角色

### 3.3 更新角色

**PUT** `/roles/{role_id}`

更新角色信息

### 3.4 删除角色

**DELETE** `/roles/{role_id}`

删除指定角色

---

## 4. 权限管理

### 4.1 获取权限列表

**GET** `/permissions`

获取权限列表

### 4.2 创建权限

**POST** `/permissions`

创建新权限

### 4.3 更新权限

**PUT** `/permissions/{permission_id}`

更新权限信息

### 4.4 删除权限

**DELETE** `/permissions/{permission_id}`

删除指定权限

---

## 5. 用户关系管理

### 5.1 用户角色管理

**POST** `/user-relations/users/{user_id}/roles` - 为用户分配角色
**GET** `/user-relations/users/{user_id}/roles` - 获取用户角色列表  
**DELETE** `/user-relations/users/{user_id}/roles/remove` - 移除用户角色

### 5.2 用户权限管理

**POST** `/user-relations/users/{user_id}/permissions` - 为用户分配权限
**GET** `/user-relations/users/{user_id}/permissions` - 获取用户权限列表  
**DELETE** `/user-relations/users/{user_id}/permissions/remove` - 移除用户权限

### 5.3 角色用户管理

**GET** `/user-relations/roles/{role_id}/users` - 获取角色下的用户列表  
**POST** `/user-relations/roles/{role_id}/users/assign` - 为角色分配用户
**DELETE** `/user-relations/roles/{role_id}/users/remove` - 从角色移除用户

### 5.4 批量操作

**POST** `/user-relations/batch/users/roles/assign` - 批量分配用户角色  
**POST** `/user-relations/batch/users/permissions/assign` - 批量分配用户权限

---

## 6. 设备管理

### 6.1 获取设备列表

**GET** `/devices`

获取设备列表，支持分页和多种过滤条件

**查询参数**:
- `page`: 页码 (默认: 1)
- `page_size`: 每页数量 (默认: 10)
- `hostname`: 设备主机名
- `ip_address`: IP地址过滤
- `device_type`: 设备类型过滤 (switch/router/firewall)
- `network_layer`: 网络层级过滤 (access/aggregation/core)
- `vendor_id`: 厂商ID过滤
- `region_id`: 基地ID过滤
- `is_active`: 是否激活

**响应**:
```json
{
  "code": 200,
  "message": "成功",
  "data": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "hostname": "SW-CD-01",
      "ip_address": "192.168.1.100",
      "device_type": "switch",
      "network_layer": "access",
      "model": "S5130-28S-HPWR-EI",
      "serial_number": "210235A1ABC123456789",
      "location": "机房A-机柜01-U1-U2",
      "ssh_port": 22,
      "auth_type": "dynamic",
      "is_active": true,
      "vendor": {
        "id": "vendor-uuid",
        "name": "华三",
        "code": "h3c"
      },
      "region": {
        "id": "region-uuid",
        "name": "成都基地",
        "code": "CD"
      },
      "created_at": "2025-01-01T00:00:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 10,
  "timestamp": "2025-08-01T12:00:00.000Z"
}
```

### 6.2 获取设备详情

**GET** `/devices/{device_id}`

获取指定设备的详细信息

### 6.3 创建设备

**POST** `/devices`

创建新设备

### 6.4 更新设备

**PUT** `/devices/{device_id}`

更新设备信息

### 6.5 删除设备

**DELETE** `/devices/{device_id}`

删除指定设备（软删除）

### 6.6 批量操作

**POST** `/devices/batch` - 批量创建设备  
**PUT** `/devices/batch` - 批量更新设备  
**DELETE** `/devices/batch` - 批量删除设备

---

## 7. 基地管理

### 7.1 获取基地列表

**GET** `/regions`

获取基地列表

### 7.2 创建基地

**POST** `/regions`

创建新基地

### 7.3 更新基地

**PUT** `/regions/{region_id}`

更新基地信息

### 7.4 删除基地

**DELETE** `/regions/{region_id}`

删除指定基地

---

## 8. 厂商管理

### 8.1 获取厂商列表

**GET** `/vendors`

获取厂商列表

### 8.2 根据代码获取厂商

**GET** `/vendors/code/{vendor_code}`

根据厂商代码获取厂商信息

### 8.3 创建厂商

**POST** `/vendors`

创建新厂商

### 8.4 更新厂商

**PUT** `/vendors/{vendor_id}`

更新厂商信息

### 8.5 删除厂商

**DELETE** `/vendors/{vendor_id}`

删除指定厂商

---

## 9. 厂商命令管理

### 9.1 获取厂商命令列表

**GET** `/vendor-commands`

获取厂商命令列表

### 9.2 创建厂商命令

**POST** `/vendor-commands`

创建新的厂商命令映射

### 9.3 更新厂商命令

**PUT** `/vendor-commands/{command_id}`

更新厂商命令

### 9.4 删除厂商命令

**DELETE** `/vendor-commands/{command_id}`

删除厂商命令

### 9.5 批量操作

**POST** `/vendor-commands/batch` - 批量创建命令  
**DELETE** `/vendor-commands/batch` - 批量删除命令

### 9.6 统计信息

**GET** `/vendor-commands/statistics/overview`

获取厂商命令统计信息

---

## 10. 设备连接与认证

### 10.1 测试设备连接

**POST** `/device-connection/test/{device_id}`

测试单个设备连接

**路径参数**:
- `device_id`: 设备ID (UUID)

**请求体**:
```json
{
  "dynamic_password": "password123"
}
```

**响应**:
```json
{
  "code": 200,
  "message": "连接测试完成",
  "data": {
    "device_id": "123e4567-e89b-12d3-a456-426614174000",
    "hostname": "SW-CD-01",
    "ip_address": "192.168.1.100",
    "connection_success": true,
    "execution_time": 2.5,
    "message": "连接成功",
    "test_time": "2025-01-01T12:00:00Z"
  },
  "timestamp": "2025-08-01T12:00:00.000Z"
}
```

### 10.2 批量测试设备连接

**POST** `/device-connection/test/batch`

批量测试设备连接

### 10.3 按条件批量测试

**POST** `/device-connection/test/by-criteria`

根据条件批量测试设备连接

### 10.4 验证设备凭据

**POST** `/device-connection/validate/{device_id}`

验证设备认证凭据

### 10.5 获取连接池统计

**GET** `/device-connection/pool/stats`

获取连接池统计信息

---

## 11. 网络查询

### 11.1 统一网络查询

**POST** `/network-query/execute`

统一的网络查询接口，支持多种查询类型

**请求体**:
```json
{
  "query_type": "mac_address",
  "parameters": {
    "mac_address": "00:11:22:33:44:55",
    "device_ids": ["device-uuid-1", "device-uuid-2"],
    "dynamic_password": "password123"
  }
}
```

**查询类型说明**:
- `template`: 基于查询模板
- `template_type`: 基于模板类型
- `mac_address`: MAC地址查询
- `interface_status`: 接口状态查�?
- `custom_command`: 自定义命�?

### 11.2 MAC地址查询

**POST** `/network-query/mac-address`

MAC地址查询�?

### 11.3 接口状态查�?

**POST** `/network-query/interface-status`

接口状态查询�?

### 11.4 自定义命令查�?

**POST** `/network-query/custom-command`

执行自定义命令�?

### 11.5 获取查询结果

**GET** `/network-query/results/{query_id}`

获取查询结果详情�?

### 11.6 获取可用模板

**GET** `/network-query/templates/available`

获取当前用户可用的查询模板列表�?

---

## 12. 查询模板管理

### 12.1 获取查询模板列表

**GET** `/query-templates`

获取查询模板列表�?

### 12.2 创建查询模板

**POST** `/query-templates`

创建新的查询模板�?

### 12.3 更新查询模板

**PUT** `/query-templates/{template_id}`

更新查询模板�?

### 12.4 删除查询模板

**DELETE** `/query-templates/{template_id}`

删除查询模板�?

### 12.5 获取模板类型

**GET** `/query-templates/types`

获取所有可用的模板类型�?

---

## 13. 查询历史管理

### 13.1 获取查询历史列表

**GET** `/query-history`

获取查询历史记录列表�?

### 13.2 获取查询历史详情

**GET** `/query-history/{history_id}`

获取查询历史详细信息�?

### 13.3 删除查询历史

**DELETE** `/query-history/{history_id}`

删除指定的查询历史记录�?

### 13.4 导出查询历史

**POST** `/query-history/export`

导出查询历史为Excel文件�?

---

## 14. 设备配置管理

### 14.1 获取设备配置列表

**GET** `/device-configs`

获取设备配置列表�?

### 14.2 获取设备配置详情

**GET** `/device-configs/{config_id}`

获取设备配置详细信息�?

### 14.3 创建设备配置

**POST** `/device-configs`

创建新的设备配置记录�?

### 14.4 备份设备配置

**POST** `/device-configs/device/{device_id}/backup`

备份指定设备的配置�?

---

## 15. 导入导出

### 15.1 生成设备导入模板

**POST** `/import-export/devices/template`

生成设备数据导入模板。

**请求体** (form-data):
- `file_format`: 文件格式 (xlsx/csv)

**响应**: 下载模板文件

### 15.2 导入设备数据

**POST** `/import-export/devices/import`

导入设备数据。

**请求体** (form-data):
- `file`: 上传的文件(xlsx/csv)
- `update_existing`: 是否更新已存在的设备 (boolean)

**响应**:
```json
{
  "message": "导入完成",
  "success_count": 10,
  "error_count": 2,
  "errors": [
    "第3行：设备主机名不能为空",
    "第5行：IP地址格式错误"
  ],
  "imported_ids": ["device-uuid-1", "device-uuid-2"]
}
```

### 15.3 导出设备数据

**POST** `/import-export/devices/export`

导出设备数据。

**请求体** (form-data):
- `file_format`: 文件格式 (xlsx/csv)

**响应**: 下载设备数据文件

---

## 16. CLI终端

### 16.1 WebSocket连接

**WebSocket** `/cli-terminal/ws/{device_id}`

建立与设备的CLI终端WebSocket连接。

**路径参数**:
- `device_id`: 设备ID (UUID)

**查询参数**:
- `token`: JWT认证token
- `dynamic_password`: 动态密码（可选）

### 16.2 获取会话统计

**GET** `/cli-terminal/sessions/stats`

获取CLI会话统计信息。

---

## 17. 操作日志管理

### 17.1 获取操作日志列表

**GET** `/operation-logs`

获取操作日志列表�?

### 17.2 获取操作日志详情

**GET** `/operation-logs/{log_id}`

获取操作日志详细信息�?

### 17.3 导出操作日志

**POST** `/operation-logs/export`

导出操作日志为Excel文件�?

### 17.4 获取操作统计

**GET** `/operation-logs/statistics`

获取操作日志统计信息�?

---

## 18. 权限缓存管理

### 18.1 刷新权限缓存

**POST** `/permission-cache/refresh`

刷新权限缓存�?

### 18.2 清空权限缓存

**DELETE** `/permission-cache/clear`

清空权限缓存�?

### 18.3 获取缓存统计

**GET** `/permission-cache/stats`

获取权限缓存统计信息�?

---

## 19. 系统统计

### 19.1 获取整体统计

**GET** `/statistics/overall`

获取系统整体统计信息�?

**查询参数**:
- `period`: 统计周期 (day/week/month/year)

**响应**:
```json
{
  "code": 200,
  "message": "成功",
  "data": {
    "user_stats": {
      "total_users": 50,
      "active_users": 45,
      "new_users_today": 2
    },
    "device_stats": {
      "total_devices": 200,
      "online_devices": 180,
      "devices_by_type": {
        "switch": 150,
        "router": 30,
        "firewall": 20
      }
    },
    "query_stats": {
      "total_queries": 1500,
      "successful_queries": 1425,
      "queries_today": 45,
      "success_rate": 95.0
    },
    "system_stats": {
      "uptime_days": 30,
      "total_operations": 5000,
      "operations_today": 120,
      "cache_hit_rate": 88.5,
      "active_sessions": 15
    }
  },
  "timestamp": "2025-08-01T12:00:00.000Z"
}
```

### 19.2 获取API统计

**GET** `/statistics/api`

获取API调用统计信息�?

### 19.3 获取模块统计

**GET** `/statistics/modules`

获取各模块使用统计�?

### 19.4 获取仪表板统�?

**GET** `/statistics/dashboard`

获取仪表板统计数据�?

---

## 20. 后台管理

### 20.1 获取仪表板数�?

**GET** `/admin/dashboard`

获取管理员仪表板数据�?

### 20.2 管理员专用路�?

**GET** `/admin/users/statistics` - 用户统计  
**GET** `/admin/devices/statistics` - 设备统计  
**GET** `/admin/system/health` - 系统健康检�? 
**POST** `/admin/system/maintenance` - 系统维护操作

---

## 21. Web页面

### 21.1 CLI终端页面

**GET** `/web/cli-terminal`

获取CLI终端页面（需要认证）�?

### 21.2 简化版CLI终端

**GET** `/web/cli-terminal-simple`

获取简化版CLI终端页面�?

### 21.3 测试页面

**GET** `/web/cli-terminal-test`

获取无需认证的CLI终端测试页面�?

---

## 📝 通用响应格式

登录（包含表单登录）、刷新token接口响应格式按遵循准的oauth2，其他所有API响应都遵循统一的`BaseResponse`格式，通过`code`字段区分成功或错误：

### BaseResponse 基础响应格式

```json
{
  "code": 200,
  "message": "成功",
  "data": {},
  "timestamp": "2025-08-01T12:00:00.000Z"
}
```

**字段说明**:
- `code`: 响应代码（200表示成功，201表示创建成功，非2开头系列表示错误）
- `message`: 响应消息
- `data`: 响应数据（可为任意类型，失败时可能为null）
- `timestamp`: 响应时间戳（UTC时间）

### 成功响应示例

```json
{
  "code": 200,
  "message": "操作成功",
  "data": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "name": "示例数据"
  },
  "timestamp": "2025-08-01T12:00:00.000Z"
}
```

### 错误响应示例

```json
{
  "code": 400,
  "message": "请求参数错误",
  "data": null,
  "timestamp": "2025-08-01T12:00:00.000Z"
}
```

### PaginatedResponse 分页响应格式

```json
{
  "code": 200,
  "message": "成功",
  "data": [
    {
      "id": "item1",
      "name": "项目1"
    }
  ],
  "total": 100,
  "page": 1,
  "page_size": 10,
  "timestamp": "2025-08-01T12:00:00.000Z"
}
```

**分页字段说明**:
- `data`: 当前页数据列表
- `total`: 总记录数
- `page`: 当前页码
- `page_size`: 每页大小
- `total_pages`: 总页数（计算得出：(total + page_size - 1) // page_size）
- `has_next`: 是否有下一页（计算得出：page < total_pages）
- `has_prev`: 是否有上一页（计算得出：page > 1）
```

---

## 🔐 认证说明

大部分API接口需要JWT认证，在请求头中添加：

```
Authorization: Bearer <access_token>
```

### 权限控制

每个接口都有对应的权限要求，确保用户具有相应权限：

- `user_management`: 用户管理权限
- `device_management`: 设备管理权限  
- `network_query`: 网络查询权限
- `system_admin`: 系统管理权限

---

## 📊 状态码说明

- `200`: 请求成功
- `201`: 创建成功
- `400`: 请求参数错误
- `401`: 未认证
- `403`: 无权限
- `404`: 资源不存在
- `422`: 数据验证失败
- `500`: 服务器内部错误
