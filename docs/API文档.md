# 网络自动化平台 API 文档

## 概述

本文档描述了网络自动化平台的所有 RESTful API 接口。平台提供了完整的网络设备管理、用户权限管理、设备连接管理、网络查询、配置管理等功能。

## 基础信息

- **基础URL**: `/api/v1`
- **认证方式**: JWT Bearer Token
- **数据格式**: JSON
- **字符编码**: UTF-8
- **API版本**: OpenAPI 3.1.0

## API 分组

### 1. 用户认证模块 (`/auth`)

#### 1.1 用户登录
- **接口**: `POST /api/v1/auth/login`
- **描述**: 用户登录获取访问令牌
- **权限**: 无需权限
- **请求体**:
```json
{
  "username": "string",
  "password": "string"
}
```
- **响应**: 返回JWT令牌和用户信息

#### 1.2 表单登录
- **接口**: `POST /api/v1/auth/login/form`
- **描述**: OAuth2表单登录
- **权限**: 无需权限
- **请求体**: `application/x-www-form-urlencoded`
- **限流**: 每分钟最多5次请求

#### 1.3 用户登出
- **接口**: `POST /api/v1/auth/logout`
- **描述**: 用户登出，使令牌失效
- **权限**: 需要认证

#### 1.4 刷新令牌
- **接口**: `POST /api/v1/auth/refresh`
- **描述**: 使用刷新令牌获取新的访问令牌
- **权限**: 无需权限

#### 1.5 获取用户信息
- **接口**: `GET /api/v1/auth/profile`
- **描述**: 获取当前用户详细信息
- **权限**: 需要认证

#### 1.6 更新用户信息
- **接口**: `PUT /api/v1/auth/profile`
- **描述**: 更新当前用户信息
- **权限**: 需要认证

#### 1.7 修改密码
- **接口**: `PUT /api/v1/auth/password`
- **描述**: 修改当前用户密码
- **权限**: 需要认证

### 2. 设备认证管理模块 (`/authentication`)

#### 2.1 认证凭据管理
- **获取设备认证凭据**: `GET /authentication/credentials/{device_id}` - 权限: `device:read`
- **验证认证凭据**: `POST /authentication/validate-credentials` - 权限: `device:read`
- **生成动态用户名**: `POST /authentication/username/generate` - 权限: `device:read`

#### 2.2 认证测试
- **测试单个设备认证**: `POST /authentication/test/{device_id}` - 权限: `device:read`
- **批量测试设备认证**: `POST /authentication/test/batch` - 权限: `device:read`

#### 2.3 缓存管理
- **清除动态密码缓存**: `POST /authentication/cache/clear` - 权限: `device:admin`
- **获取缓存信息**: `GET /authentication/cache/info` - 权限: `device:read`
- **获取认证配置**: `GET /authentication/config` - 权限: `device:read`

### 3. 设备连接管理模块 (`/device-connection`)

#### 3.1 连接测试
- **测试单个设备连接**: `POST /device-connection/test` - 权限: `device:read`
- **批量测试设备连接**: `POST /device-connection/test/batch` - 权限: `device:read`
- **测试连接稳定性**: `POST /device-connection/test/stability` - 权限: `device:read`
- **按条件批量测试**: `POST /device-connection/test/by-criteria` - 权限: `device:read`

#### 3.2 连接池管理
- **获取连接池统计**: `GET /device-connection/pool/stats` - 权限: `device:read`
- **获取连接管理器统计**: `GET /device-connection/manager/stats` - 权限: `device:read`
- **清理空闲连接**: `POST /device-connection/pool/cleanup` - 权限: `device:admin`
- **关闭设备连接**: `DELETE /device-connection/close/{device_id}` - 权限: `device:admin`
- **启动连接池**: `POST /device-connection/pool/start` - 权限: `device:admin`
- **停止连接池**: `POST /device-connection/pool/stop` - 权限: `device:admin`

#### 3.3 凭据和密码管理
- **验证认证凭据**: `POST /device-connection/validate-credentials` - 权限: `device:read`
- **密码加密**: `POST /device-connection/encrypt-password` - 权限: `device:admin`
- **清除动态密码缓存**: `DELETE /device-connection/cache/password` - 权限: `device:admin`
- **获取缓存密码信息**: `GET /device-connection/cache/password/info` - 权限: `device:read`

### 4. 用户管理模块 (`/users`)

#### 4.1 用户基础操作
- **获取用户列表**: `GET /users` - 权限: `user:read`
- **获取用户详情**: `GET /users/{user_id}` - 权限: `user:read`
- **创建用户**: `POST /users` - 权限: `user:create`
- **更新用户**: `PUT /users/{user_id}` - 权限: `user:update`
- **删除用户**: `DELETE /users/{user_id}` - 权限: `user:delete`
- **更新用户状态**: `PUT /users/{user_id}/status` - 权限: `user:update`

#### 4.2 用户角色管理
- **分配用户角色（全量）**: `POST /users/{user_id}/roles` - 权限: `user:assign_roles`
- **添加用户角色（增量）**: `POST /users/{user_id}/roles/add` - 权限: `user:assign_roles`
- **移除用户角色**: `DELETE /users/{user_id}/roles/remove` - 权限: `user:assign_roles`
- **获取用户角色列表**: `GET /users/{user_id}/roles` - 权限: `user:read`

#### 4.3 用户权限管理
- **设置用户权限（全量）**: `POST /users/{user_id}/permissions` - 权限: `user:assign_permissions`
- **添加用户权限（增量）**: `POST /users/{user_id}/permissions/add` - 权限: `user:assign_permissions`
- **移除用户权限**: `DELETE /users/{user_id}/permissions/remove` - 权限: `user:assign_permissions`
- **获取用户权限列表**: `GET /users/{user_id}/permissions` - 权限: `user:read`

### 5. 角色管理模块 (`/roles`)

#### 5.1 角色基础操作
- **获取角色列表**: `GET /api/v1/roles` - 权限: `role:read`
- **获取角色详情**: `GET /api/v1/roles/{role_id}` - 权限: `role:read`
- **创建角色**: `POST /api/v1/roles` - 权限: `role:create`
- **更新角色**: `PUT /api/v1/roles/{role_id}` - 权限: `role:update`
- **删除角色**: `DELETE /api/v1/roles/{role_id}` - 权限: `role:delete`
- **更新角色状态**: `PUT /api/v1/roles/{role_id}/status` - 权限: `role:update`

#### 5.2 角色权限管理
- **分配角色权限（全量）**: `POST /api/v1/roles/{role_id}/permissions` - 权限: `role:assign_permissions`
- **添加角色权限（增量）**: `POST /api/v1/roles/{role_id}/permissions/add` - 权限: `role:assign_permissions`
- **移除角色权限**: `DELETE /api/v1/roles/{role_id}/permissions/remove` - 权限: `role:assign_permissions`
- **获取角色权限列表**: `GET /api/v1/roles/{role_id}/permissions` - 权限: `role:read`

#### 5.3 批量操作
- **批量创建角色**: `POST /api/v1/roles/batch` - 权限: `role:create`
- **批量更新角色**: `PUT /api/v1/roles/batch` - 权限: `role:update`
- **批量删除角色**: `DELETE /api/v1/roles/batch` - 权限: `role:delete`

### 6. 权限管理模块 (`/permissions`)

#### 6.1 权限基础操作
- **获取权限列表**: `GET /api/v1/permissions` - 权限: `permission:read`
- **获取权限详情**: `GET /api/v1/permissions/{permission_id}` - 权限: `permission:read`
- **创建权限**: `POST /api/v1/permissions` - 权限: `permission:create`
- **更新权限**: `PUT /api/v1/permissions/{permission_id}` - 权限: `permission:update`
- **删除权限**: `DELETE /api/v1/permissions/{permission_id}` - 权限: `permission:delete`
- **更新权限状态**: `PUT /api/v1/permissions/{permission_id}/status` - 权限: `permission:update`

#### 6.2 批量操作
- **批量创建权限**: `POST /api/v1/permissions/batch` - 权限: `permission:create`
- **批量更新权限**: `PUT /api/v1/permissions/batch` - 权限: `permission:update`
- **批量删除权限**: `DELETE /api/v1/permissions/batch` - 权限: `permission:delete`

### 7. 设备管理模块 (`/devices`)

#### 7.1 设备基础操作
- **获取设备列表**: `GET /api/v1/devices` - 权限: `device:read`
- **获取设备详情**: `GET /api/v1/devices/{device_id}` - 权限: `device:read`
- **创建设备**: `POST /api/v1/devices` - 权限: `device:create`
- **更新设备**: `PUT /api/v1/devices/{device_id}` - 权限: `device:update`
- **删除设备**: `DELETE /api/v1/devices/{device_id}` - 权限: `device:delete`

#### 7.2 设备连接测试
- **测试设备连接**: `POST /api/v1/devices/{device_id}/test-connection` - 权限: `device:connection_test`

#### 7.3 批量操作
- **批量创建设备**: `POST /api/v1/devices/batch` - 权限: `device:create`
- **批量更新设备**: `PUT /api/v1/devices/batch` - 权限: `device:update`
- **批量删除设备**: `DELETE /api/v1/devices/batch` - 权限: `device:delete`

### 8. 设备配置管理模块 (`/device-configs`)

#### 8.1 配置基础操作
- **获取配置列表**: `GET /api/v1/device-configs` - 权限: `config:read`
- **获取配置详情**: `GET /api/v1/device-configs/{config_id}` - 权限: `config:read`
- **创建配置**: `POST /api/v1/device-configs` - 权限: `config:create`
- **更新配置**: `PUT /api/v1/device-configs/{config_id}` - 权限: `config:update`
- **删除配置**: `DELETE /api/v1/device-configs/{config_id}` - 权限: `config:delete`

#### 8.2 配置比较和历史
- **比较设备配置**: `POST /api/v1/device-configs/compare` - 权限: `config:read`
- **获取设备最新配置**: `GET /api/v1/device-configs/device/{device_id}/latest` - 权限: `config:read`
- **获取设备配置历史**: `GET /api/v1/device-configs/device/{device_id}/history` - 权限: `config:read`
- **获取设备配置变更**: `GET /api/v1/device-configs/device/{device_id}/changes` - 权限: `config:read`

#### 8.3 批量操作
- **批量备份设备配置**: `POST /api/v1/device-configs/batch/backup` - 权限: `config:create`
- **批量创建配置**: `POST /api/v1/device-configs/batch` - 权限: `config:create`
- **批量更新配置**: `PUT /api/v1/device-configs/batch` - 权限: `config:update`
- **批量删除配置**: `DELETE /api/v1/device-configs/batch` - 权限: `config:delete`

#### 8.4 配置管理
- **清理旧配置**: `POST /api/v1/device-configs/cleanup` - 权限: `config:delete`
- **获取配置统计**: `GET /api/v1/device-configs/statistics` - 权限: `config:read`
- **搜索设备配置**: `GET /api/v1/device-configs/search` - 权限: `config:read`
- **验证配置内容**: `POST /api/v1/device-configs/validate` - 权限: `config:read`

### 9. 基地管理模块 (`/regions`)

#### 9.1 基地基础操作
- **获取基地列表**: `GET /api/v1/regions` - 权限: `region:read`
- **创建基地**: `POST /api/v1/regions` - 权限: `region:create`
- **获取基地详情**: `GET /api/v1/regions/{region_id}` - 权限: `region:read`
- **更新基地**: `PUT /api/v1/regions/{region_id}` - 权限: `region:update`
- **删除基地**: `DELETE /api/v1/regions/{region_id}` - 权限: `region:delete`
- **根据基地代码获取基地**: `GET /api/v1/regions/code/{region_code}` - 权限: `region:read`

#### 9.2 批量操作
- **批量更新基地**: `PUT /api/v1/regions/batch` - 权限: `region:update`
- **批量创建基地**: `POST /api/v1/regions/batch` - 权限: `region:create`
- **批量删除基地**: `DELETE /api/v1/regions/batch` - 权限: `region:delete`

### 10. 厂商管理模块 (`/vendors`)

#### 10.1 厂商基础操作
- **获取厂商列表**: `GET /api/v1/vendors` - 权限: `vendor:read`
- **创建厂商**: `POST /api/v1/vendors` - 权限: `vendor:create`
- **获取厂商详情**: `GET /api/v1/vendors/{vendor_id}` - 权限: `vendor:read`
- **更新厂商**: `PUT /api/v1/vendors/{vendor_id}` - 权限: `vendor:update`
- **删除厂商**: `DELETE /api/v1/vendors/{vendor_id}` - 权限: `vendor:delete`
- **根据厂商代码获取厂商**: `GET /api/v1/vendors/code/{vendor_code}` - 权限: `vendor:read`

#### 10.2 批量操作
- **批量更新厂商**: `PUT /api/v1/vendors/batch` - 权限: `vendor:update`
- **批量创建厂商**: `POST /api/v1/vendors/batch` - 权限: `vendor:create`
- **批量删除厂商**: `DELETE /api/v1/vendors/batch` - 权限: `vendor:delete`

### 11. 厂商命令管理模块 (`/vendor_commands`)

#### 11.1 基础命令操作
- **获取厂商命令列表**: `GET /api/v1/vendor_commands` - 权限: `vendor:read`
- **创建厂商命令**: `POST /api/v1/vendor_commands` - 权限: `vendor:create`
- **获取厂商命令详情**: `GET /api/v1/vendor_commands/{command_id}` - 权限: `vendor:read`
- **更新厂商命令**: `PUT /api/v1/vendor_commands/{command_id}` - 权限: `vendor:update`
- **删除厂商命令**: `DELETE /api/v1/vendor_commands/{command_id}` - 权限: `vendor:delete`

#### 11.2 批量操作
- **批量创建厂商命令**: `POST /api/v1/vendor_commands/batch` - 权限: `vendor:create`
- **批量删除厂商命令**: `DELETE /api/v1/vendor_commands/batch` - 权限: `vendor:delete`
- **批量更新命令状态**: `PUT /api/v1/vendor_commands/batch/status` - 权限: `vendor:update`
- **获取命令统计概览**: `GET /api/v1/vendor_commands/statistics/overview` - 权限: `vendor:read`

### 12. 查询模板管理模块 (`/query_templates`)

#### 12.1 基础模板操作
- **获取查询模板列表**: `GET /api/v1/query_templates` - 权限: `template:read`
- **创建查询模板**: `POST /api/v1/query_templates` - 权限: `template:create`
- **获取查询模板详情**: `GET /api/v1/query_templates/{template_id}` - 权限: `template:read`
- **更新查询模板**: `PUT /api/v1/query_templates/{template_id}` - 权限: `template:update`
- **删除查询模板**: `DELETE /api/v1/query_templates/{template_id}` - 权限: `template:delete`

#### 12.2 批量操作
- **批量更新查询模板**: `PUT /api/v1/query_templates/batch` - 权限: `template:update`
- **批量创建查询模板**: `POST /api/v1/query_templates/batch` - 权限: `template:create`
- **批量删除查询模板**: `DELETE /api/v1/query_templates/batch` - 权限: `template:delete`

### 13. 查询历史管理模块 (`/query_history`)

#### 13.1 基础历史操作
- **获取查询历史列表**: `GET /api/v1/query_history` - 权限: `history:read`
- **创建查询历史**: `POST /api/v1/query_history` - 权限: `history:create`
- **获取查询历史详情**: `GET /api/v1/query_history/{history_id}` - 权限: `history:read`
- **删除查询历史**: `DELETE /api/v1/query_history/{history_id}` - 权限: `history:delete`

#### 13.2 批量操作和统计
- **批量创建查询历史**: `POST /api/v1/query_history/batch` - 权限: `history:create`
- **批量删除查询历史**: `DELETE /api/v1/query_history/batch` - 权限: `history:delete`
- **获取最近查询历史**: `GET /api/v1/query_history/recent` - 权限: `history:read`
- **获取查询历史统计**: `GET /api/v1/query_history/statistics` - 权限: `history:read`
- **清理旧查询历史**: `DELETE /api/v1/query_history/cleanup` - 权限: `history:delete`

### 14. 网络查询模块 (`/network_query`)

#### 14.1 查询执行
- **执行网络查询**: `POST /api/v1/network_query/execute` - 权限: `query:execute`
- **根据IP执行网络查询**: `POST /api/v1/network_query/execute_by_ip` - 权限: `query:execute`
- **MAC地址查询**: `POST /api/v1/network_query/mac_query` - 权限: `query:execute`
- **接口状态查询**: `POST /api/v1/network_query/interface_status` - 权限: `query:execute`
- **执行自定义命令**: `POST /api/v1/network_query/custom_commands` - 权限: `query:execute`

#### 14.2 模板和健康检查
- **获取可用模板**: `GET /api/v1/network_query/templates` - 权限: `query:read`
- **健康检查**: `GET /api/v1/network_query/health` - 权限: 无需权限

### 15. 导入导出模块 (`/import_export`)

#### 15.1 设备导入导出
- **生成设备模板**: `POST /api/v1/import_export/devices/template` - 权限: `device:read`
- **导入设备**: `POST /api/v1/import_export/devices/import` - 权限: `device:create`
- **导出设备**: `POST /api/v1/import_export/devices/export` - 权限: `device:read`

### 16. 系统监控模块

#### 16.1 健康检查和指标
- **健康检查**: `GET /health` - 权限: 无需权限
- **获取系统指标**: `GET /metrics` - 权限: 无需权限
- **根路径**: `GET /` - 权限: 无需权限

## 通用特性

### 分页查询
所有列表接口都支持分页查询，通用参数：
- `page`: 页码（从1开始）
- `page_size`: 每页大小
- `search`: 搜索关键词
- 其他筛选条件根据具体模块而定

### 批量操作
大部分模块都支持批量操作：
- 批量创建：`POST /{module}/batch`
- 批量更新：`PUT /{module}/batch`
- 批量删除：`DELETE /{module}/batch`

### 权限控制
所有接口都通过 `require_permission` 装饰器进行权限控制，权限格式为 `{module}:{action}`：
- `read`: 读取权限
- `create`: 创建权限
- `update`: 更新权限
- `delete`: 删除权限
- 其他特殊权限根据具体功能定义

### 响应格式

#### 成功响应
```json
{
  "success": true,
  "message": "操作成功",
  "data": {},
  "timestamp": "2025-01-XX 10:00:00"
}
```

#### 分页响应
```json
{
  "data": [],
  "total": 100,
  "page": 1,
  "page_size": 20
}
```

#### 错误响应
```json
{
  "success": false,
  "message": "错误信息",
  "detail": "详细错误描述",
  "timestamp": "2025-01-XX 10:00:00"
}
```

### HTTP 状态码
- `200`: 操作成功
- `201`: 创建成功
- `400`: 请求参数错误
- `401`: 未认证
- `403`: 权限不足
- `404`: 资源不存在
- `500`: 服务器内部错误

## 安全特性

### JWT认证
- 所有需要认证的接口都使用JWT Bearer Token
- 支持访问令牌和刷新令牌机制
- 令牌自动过期和刷新
- OAuth2 兼容的表单登录支持

### 权限控制
- 基于RBAC模型的细粒度权限控制
- 支持用户、角色、权限的灵活组合
- 权限继承和权限检查机制
- 实时权限验证和缓存优化

### 操作审计
- 完整的操作日志记录和管理
- 支持日志统计和清理功能
- 操作追溯和安全审计
- 用户行为分析和监控

### 数据安全
- 软删除机制保护重要数据
- 密码加密存储和传输
- 敏感信息脱敏处理
- 数据完整性验证

### 缓存管理
- 多层级权限缓存机制
- 动态密码缓存管理
- 连接池状态缓存
- 缓存失效和清理策略

## 网络自动化特色功能

### 设备管理
- **多品牌支持**: 华为、思科、华三等主流网络设备
- **统一接口**: 标准化的设备管理API
- **批量操作**: 支持设备的批量创建、更新、删除
- **设备分组**: 按基地、厂商、类型等维度管理

### 认证管理
- **动态认证**: 支持动态密码和静态密码认证
- **智能缓存**: 动态密码缓存和自动清理
- **批量测试**: 支持批量设备认证测试
- **用户名生成**: 基于规则的动态用户名生成

### 连接管理
- **连接池**: 高性能设备连接池管理
- **稳定性测试**: 连接稳定性和质量监控
- **并发控制**: 可配置的并发连接数量
- **状态监控**: 实时连接状态和统计信息

### 配置管理
- **版本控制**: 设备配置的版本管理和历史记录
- **差异对比**: 配置变更对比和分析
- **批量备份**: 支持批量配置备份和恢复
- **配置验证**: 配置内容的有效性验证

### 网络查询
- **多种查询**: 支持MAC查询、接口状态、自定义命令
- **查询模板**: 可配置的查询模板管理
- **历史记录**: 查询历史记录和统计分析
- **IP查询**: 支持基于IP地址的设备查询

### 数据管理
- **导入导出**: 设备数据的批量导入导出
- **模板生成**: 标准化的数据模板生成
- **厂商管理**: 网络设备厂商和命令管理
- **基地管理**: 网络基地和区域管理

### 系统监控
- **健康检查**: 系统和服务健康状态监控
- **性能指标**: 系统性能和资源使用监控
- **统计分析**: 多维度的数据统计和分析
- **管理面板**: 综合的管理仪表板

---

**文档说明**: 
- 本文档基于OpenAPI 3.1.0规范生成
- 包含网络自动化平台的所有API接口（共120+个接口）
- 涵盖认证、用户管理、设备管理、网络查询、配置管理等核心功能
- 如有接口变更，请参考最新的openapi.json文件