# AutoNetwork API 文档

## 基础 URL：`http://localhost:8000/api`
## 版本前缀：`/v1`

# AutoNetwork API 文档

## 基础 URL：`http://localhost:8000/api`
## 版本前缀：`/v1`

## ⚠️ 重要更新说明

本文档反映了API接口重构和统计功能整合后的最新状态：

### 🔄 API整合变更
1. **设备认证功能合并**：原 `/authentication` 接口已合并到 `/device-connection`
2. **网络查询功能合并**：原 `/network-query` 接口已合并到 `/universal-query`
3. **统计功能统一**：所有统计端点统一到 `/stats` 模块，消除分散的统计接口
4. **健康检查统一**：系统健康检查统一到根路径 `/health` 接口

### 📍 迁移路径
- `POST /authentication/*` → `POST /device-connection/auth/*`
- `POST /network-query/mac` → `POST /universal-query/mac`（推荐）或 `POST /universal-query/legacy/mac-query`（兼容）
- `POST /network-query/interface-status` → `POST /universal-query/interface-status`（推荐）或 `POST /universal-query/legacy/interface-status`（兼容）
- `POST /devices/{device_id}/test-connection` → `POST /device-connection/test`
- **统计接口迁移**：
  - `GET /device-connection/pool/stats` → `GET /stats/connections`
  - `GET /device-connection/manager/stats` → `GET /stats/connections`
  - `GET /universal-query/stats` → `GET /stats/queries`
  - `GET /permission-cache/stats` → `GET /stats/permissions`
  - `GET /cli-terminal/sessions/stats` → `GET /stats/cli-sessions`
  - `GET /admin-dashboard/stats` → `GET /stats/dashboard`

## 接口列表

### 🔐 认证管理 (auth.py)
- POST /auth/login: 用户登录
- POST /auth/login/form: 表单登录
- POST /auth/refresh: 刷新令牌
- POST /auth/logout: 用户登出
- GET /auth/me: 获取当前用户信息

### 📊 系统统计 (statistics.py) - **🆕 统一统计入口**
> **重要说明**：所有统计功能已统一到此模块，其他模块的统计端点已被移除

- GET /stats/overall: 获取整体统计信息
- GET /stats/api: 获取API统计信息
- GET /stats/modules: 获取模块统计信息
- GET /stats/dashboard: 获取仪表板统计信息
- GET /stats/connections: 获取设备连接统计信息（原device-connection模块）
- GET /stats/queries: 获取查询引擎统计信息（原universal-query模块）
- GET /stats/permissions: 获取权限缓存统计信息（原permission-cache模块）
- GET /stats/cli-sessions: 获取CLI会话统计信息（原cli-terminal模块）

### 🔧 后台管理仪表板 (admin_dashboard.py)
- POST /admin/permissions/check: 检查用户权限
- GET /admin/permissions/inheritance/{user_id}: 获取用户权限继承关系
- POST /admin/quick-actions/batch-enable-users: 批量启用用户
- POST /admin/quick-actions/batch-disable-users: 批量禁用用户
- GET /admin/export/users: 导出用户数据
- GET /admin/export/roles: 导出角色数据

### 🌐 设备连接与认证管理 (device_connection.py) 
> **重要说明**：统计功能已迁移到 `/stats/connections`

#### 连接测试功能
- POST /device-connection/test: 测试单个设备连接
- POST /device-connection/test/batch: 批量测试设备连接
- POST /device-connection/test/stability: 测试设备连接稳定性
- POST /device-connection/test/criteria: 根据条件批量测试设备

#### 认证管理功能（原authentication.py迁移）
- GET /device-connection/credentials/{device_id}: 获取设备认证凭据
- POST /device-connection/credentials/validate: 验证设备认证凭据
- POST /device-connection/auth/credentials: 获取设备认证凭据
- POST /device-connection/auth/test: 测试设备认证
- POST /device-connection/auth/test/batch: 批量测试设备认证
- POST /device-connection/auth/username/generate: 生成动态用户名
- GET /device-connection/auth/config: 获取认证配置信息

#### 连接池管理
- POST /device-connection/pool/cleanup: 清理空闲连接
- POST /device-connection/pool/start: 启动连接池
- POST /device-connection/pool/stop: 停止连接池
- DELETE /device-connection/close/{device_id}: 关闭设备连接

#### 密码管理
- POST /device-connection/password/encrypt: 加密设备密码
- DELETE /device-connection/cache/password/clear: 清除动态密码缓存
- GET /device-connection/cache/password/info/unified: 获取缓存密码信息

### 💻 CLI 终端 (cli_terminal.py)
> **重要说明**：统计功能已迁移到 `/stats/cli-sessions`

- WS /cli/connect/{device_id}: 连接设备CLI终端
- WS /cli/manual-connect: 连接手动配置设备CLI终端
- GET /cli/sessions: 获取当前用户的所有CLI会话
- GET /cli/all-sessions: 获取所有CLI会话（管理员）
- DELETE /cli/sessions/{session_id}: 关闭指定的CLI会话
- GET /cli/platforms: 获取支持的设备平台列表
- POST /cli/validate-config: 验证设备连接配置
- GET /cli/sessions/{session_id}: 获取指定会话的详细信息
- POST /cli/sessions/{session_id}/reconnect: 重连指定的CLI会话

### 📋 设备配置 (device_configs.py)
#### 基础配置管理
- GET /device-configs: 获取配置快照列表
- GET /device-configs/{snapshot_id}: 获取配置快照详情
- POST /device-configs: 创建配置快照
- PUT /device-configs/{snapshot_id}: 更新配置快照
- DELETE /device-configs/{snapshot_id}: 删除配置快照

#### 配置对比与分析
- POST /device-configs/compare: 对比配置快照
- POST /device-configs/smart-compare: 智能配置差异对比
- POST /device-configs/compare-with-latest: 与最新配置对比
- GET /device-configs/change-summary: 获取配置变更摘要
- POST /device-configs/batch-compare: 批量配置对比
- POST /device-configs/export-diff: 导出差异为HTML

#### 配置历史与查询
- GET /device-configs/latest/{device_id}: 获取设备最新配置
- GET /device-configs/history/{device_id}: 获取设备配置历史
- GET /device-configs/changes/{device_id}: 获取设备配置变更
- GET /device-configs/recent: 获取最近配置
- GET /device-configs/user/{user_id}: 获取用户配置快照
- POST /device-configs/search: 搜索配置快照

#### 批量操作
- POST /device-configs/batch-backup: 批量备份设备配置
- POST /device-configs/batch-create: 批量创建配置快照
- PUT /device-configs/batch-update: 批量更新配置快照
- DELETE /device-configs/batch-delete: 批量删除配置快照

#### 配置回滚与管理
- POST /device-configs/preview-rollback: 预览配置回滚
- POST /device-configs/rollback: 执行配置回滚
- POST /device-configs/batch-rollback: 批量配置回滚
- POST /device-configs/cleanup: 清理旧配置快照
- POST /device-configs/validate: 验证配置内容

### 📱 设备管理 (devices.py)
- GET /devices: 获取设备列表
- GET /devices/{device_id}: 获取设备详情
- POST /devices: 创建设备
- PUT /devices/{device_id}: 更新设备
- DELETE /devices/{device_id}: 删除设备
- POST /devices/batch: 批量创建设备
- PUT /devices/batch: 批量更新设备
- DELETE /devices/batch: 批量删除设备

### 📁 导入导出 (import_export.py)
- GET /import-export/template: 生成设备导入模板
- POST /import-export/devices/import: 导入设备数据
- POST /import-export/devices/export: 导出设备数据

### 🔍 通用查询 (universal_query.py)
> **重要说明**：统计功能已迁移到 `/stats/queries`，健康检查已移除（使用系统统一健康检查）

#### 模板查询功能
- POST /universal-query/template: 执行基于模板的查询
- POST /universal-query/template-type: 执行基于模板类型的查询
- POST /universal-query/template/{template_id}/commands/preview: 预览模板命令
- POST /universal-query/template/{template_id}/parameters/validate: 验证模板参数

#### 便捷查询接口
- POST /universal-query/mac: MAC地址查询
- POST /universal-query/interface-status: 接口状态查询
- POST /universal-query/config: 配置显示查询

#### 原网络查询功能（兼容接口，标记为废弃）
- POST /universal-query/legacy/execute: 执行网络查询
- POST /universal-query/legacy/execute-by-ip: 根据IP执行网络查询
- POST /universal-query/legacy/mac-query: MAC地址查询（已废弃，使用 `/universal-query/mac`）
- POST /universal-query/legacy/interface-status: 接口状态查询（已废弃，使用 `/universal-query/interface-status`）
- POST /universal-query/legacy/custom-commands: 执行自定义命令
- GET /universal-query/legacy/templates: 获取可用查询模板

### 📜 操作日志 (operation_logs.py)
- GET /operation-logs: 获取操作日志列表
- GET /operation-logs/stats: 获取操作日志统计
- DELETE /operation-logs/cleanup: 清理操作日志

### 🔒 权限缓存 (permission_cache.py)
> **重要说明**：统计功能已迁移到 `/stats/permissions`

- GET /permission-cache/test/{user_id}: 测试用户权限缓存
- DELETE /permission-cache/user/{user_id}: 清除用户权限缓存
- DELETE /permission-cache/role/{role_id}: 清除角色权限缓存
- DELETE /permission-cache/all: 清除所有权限缓存

### 🛡️ 权限管理 (permissions.py)
- GET /permissions: 获取权限列表
- GET /permissions/{permission_id}: 获取权限详情
- POST /permissions: 创建权限
- PUT /permissions/{permission_id}: 更新权限
- DELETE /permissions/{permission_id}: 删除权限
- PUT /permissions/{permission_id}/status: 更新权限状态
- POST /permissions/batch-create: 批量创建权限
- PUT /permissions/batch-update: 批量更新权限
- DELETE /permissions/batch-delete: 批量删除权限

### 📖 查询历史 (query_history.py)
- GET /query-history: 获取查询历史列表
- GET /query-history/{history_id}: 获取查询历史详情
- POST /query-history: 创建查询历史
- DELETE /query-history/{history_id}: 删除查询历史
- POST /query-history/batch-create: 批量创建查询历史
- DELETE /query-history/batch-delete: 批量删除查询历史
- GET /query-history/recent: 获取最近查询历史
- GET /query-history/stats: 获取查询历史统计
- DELETE /query-history/cleanup: 清理旧查询历史

### 📝 查询模板 (query_templates.py)
#### 基础模板管理
- GET /query-templates: 获取查询模板列表
- GET /query-templates/{template_id}: 获取查询模板详情
- POST /query-templates: 创建查询模板
- PUT /query-templates/{template_id}: 更新查询模板
- DELETE /query-templates/{template_id}: 删除查询模板

#### 批量操作
- POST /query-templates/batch: 批量创建查询模板
- PUT /query-templates/batch: 批量更新查询模板
- DELETE /query-templates/batch: 批量删除查询模板

#### 模板状态管理
- PUT /query-templates/{template_id}/activate: 激活查询模板
- PUT /query-templates/{template_id}/deactivate: 停用查询模板
- PUT /query-templates/batch/activate: 批量激活/停用查询模板

#### 模板查询
- GET /query-templates/active: 获取所有激活的查询模板
- GET /query-templates/type/{template_type}: 根据类型获取查询模板
- GET /query-templates/with-commands: 获取包含厂商命令的查询模板

### 🏢 基地管理 (regions.py)
- GET /regions: 获取基地列表
- GET /regions/{region_id}: 获取基地详情
- POST /regions: 创建基地
- PUT /regions/{region_id}: 更新基地
- DELETE /regions/{region_id}: 删除基地
- POST /regions/batch: 批量创建基地
- PUT /regions/batch: 批量更新基地
- DELETE /regions/batch: 批量删除基地
- GET /regions/code/{region_code}: 根据代码获取基地

### 👥 角色管理 (roles.py)
#### 基础角色管理
- GET /roles: 获取角色列表
- GET /roles/{role_id}: 获取角色详情
- POST /roles: 创建角色
- PUT /roles/{role_id}: 更新角色
- DELETE /roles/{role_id}: 删除角色
- PUT /roles/{role_id}/status: 更新角色状态

#### 角色权限管理
- POST /roles/{role_id}/permissions: 分配角色权限
- POST /roles/{role_id}/permissions/add: 为角色添加权限
- DELETE /roles/{role_id}/permissions/remove: 移除角色权限
- GET /roles/{role_id}/permissions: 获取角色权限列表

#### 批量操作
- POST /roles/batch: 批量创建角色
- PUT /roles/batch: 批量更新角色
- DELETE /roles/batch: 批量删除角色

### 🔗 用户关系 (user_relations.py)
#### 批量用户关系管理
- POST /user-relations/batch/users/roles/assign: 批量分配用户角色
- POST /user-relations/batch/users/roles/add: 批量添加用户角色
- DELETE /user-relations/batch/users/roles/remove: 批量移除用户角色
- POST /user-relations/batch/users/permissions/assign: 批量分配用户权限

#### 角色用户管理
- GET /user-relations/roles/{role_id}/users: 获取角色下的所有用户
- POST /user-relations/roles/{role_id}/users/assign: 为角色批量分配用户
- DELETE /user-relations/roles/{role_id}/users/remove: 从角色批量移除用户

#### 权限用户管理
- GET /user-relations/permissions/{permission_id}/users: 获取权限下的所有用户

#### 用户权限汇总
- GET /user-relations/users/{user_id}/summary: 获取用户权限汇总
- POST /user-relations/users/{user_id}/roles: 为用户分配角色（统一入口）
- POST /user-relations/users/{user_id}/roles/add: 为用户添加角色（统一入口）
- GET /user-relations/users/{user_id}/roles: 获取用户角色列表（统一入口）

### 👤 用户管理 (users.py)
#### 基础用户管理
- GET /users: 获取用户列表
- GET /users/{user_id}: 获取用户详情
- POST /users: 创建用户
- PUT /users/{user_id}: 更新用户
- DELETE /users/{user_id}: 删除用户
- PUT /users/{user_id}/status: 更新用户状态

#### 用户角色管理
- POST /users/{user_id}/roles: 分配用户角色
- POST /users/{user_id}/roles/add: 为用户添加角色
- DELETE /users/{user_id}/roles/remove: 移除用户角色
- GET /users/{user_id}/roles: 获取用户角色列表

#### 用户权限管理
- POST /users/{user_id}/permissions: 设置用户权限
- POST /users/{user_id}/permissions/add: 为用户添加权限
- DELETE /users/{user_id}/permissions/remove: 移除用户权限
- GET /users/{user_id}/permissions: 获取用户权限列表

#### 批量操作
- POST /users/batch: 批量创建用户
- PUT /users/batch: 批量更新用户
- DELETE /users/batch: 批量删除用户

### ⚙️ 厂商命令 (vendor_commands.py)
- GET /vendor-commands: 获取厂商命令列表
- GET /vendor-commands/{command_id}: 获取厂商命令详情
- POST /vendor-commands: 创建厂商命令
- PUT /vendor-commands/{command_id}: 更新厂商命令
- DELETE /vendor-commands/{command_id}: 删除厂商命令
- POST /vendor-commands/batch: 批量创建厂商命令
- PUT /vendor-commands/batch/status: 批量更新命令状态
- DELETE /vendor-commands/batch: 批量删除厂商命令
- GET /vendor-commands/statistics/overview: 获取厂商命令统计信息

### 🏭 厂商管理 (vendors.py)
- GET /vendors: 获取厂商列表
- GET /vendors/{vendor_id}: 获取厂商详情
- POST /vendors: 创建厂商
- PUT /vendors/{vendor_id}: 更新厂商
- DELETE /vendors/{vendor_id}: 删除厂商
- POST /vendors/batch: 批量创建厂商
- PUT /vendors/batch: 批量更新厂商
- DELETE /vendors/batch: 批量删除厂商
- GET /vendors/code/{vendor_code}: 根据代码获取厂商

### 🌐 Web 路由 (web_routes.py)
- GET /web/cli-terminal: 获取CLI终端页面
- GET /web/cli-terminal-simple: 获取简化版CLI终端页面
- GET /web/cli-terminal-test: 获取无需认证的CLI终端测试页面

### 🔧 系统路由
- GET /: 根路由重定向
- GET /health: **统一健康检查接口** - 检查数据库、Redis、API等所有组件状态
- GET /metrics: 获取应用监控指标

## 📋 API架构说明

### 🔄 统计功能统一架构
为解决统计功能分散、路由混乱的问题，现已将所有统计相关接口统一到 `/stats` 模块：

- **统一前缀**: 所有统计接口使用 `/stats/*` 路径
- **功能整合**: 原分散在各模块的统计端点已全部迁移
- **清晰职责**: 各模块专注核心业务，统计功能集中管理

### 🔗 健康检查统一
- **统一入口**: `/health` 提供系统全面健康检查
- **组件覆盖**: 数据库、Redis、API服务、系统资源等
- **移除重复**: 删除各模块分散的健康检查端点

### 📊 接口优化成果
1. **消除重复**: 移除了8个重复的统计端点
2. **路由规范**: 统一了接口命名和路径结构
3. **职责清晰**: 各模块功能边界更加明确
4. **维护简化**: 统计逻辑集中管理，便于维护

---

**文档更新时间**: 2025-08-01
**当前版本**: API v1 (重构后)
**主要变更**: 统计功能统一、健康检查整合、API架构优化

### 设备配置 (device_configs.py)
- GET /device-configs: 获取配置快照列表
- GET /device-configs/{snapshot_id}: 获取配置快照详情
- POST /device-configs: 创建配置快照
- PUT /device-configs/{snapshot_id}: 更新配置快照
- DELETE /device-configs/{snapshot_id}: 删除配置快照
- POST /device-configs/compare: 对比配置快照
- GET /device-configs/latest/{device_id}: 获取设备最新配置
- GET /device-configs/history/{device_id}: 获取设备配置历史
- GET /device-configs/changes/{device_id}: 获取设备配置变更
- POST /device-configs/batch-backup: 批量备份设备配置
- POST /device-configs/batch-create: 批量创建配置快照
- PUT /device-configs/batch-update: 批量更新配置快照
- DELETE /device-configs/batch-delete: 批量删除配置快照
- POST /device-configs/cleanup: 清理旧配置快照
- GET /device-configs/stats: 获取配置快照统计
- POST /device-configs/search: 搜索配置快照
- GET /device-configs/recent: 获取最近配置
- GET /device-configs/user-snapshots: 获取用户配置快照
- POST /device-configs/validate: 验证配置内容
- POST /device-configs/smart-compare: 智能配置差异对比
- POST /device-configs/compare-with-latest: 与最新配置对比
- GET /device-configs/change-summary: 获取配置变更摘要
- POST /device-configs/batch-compare: 批量配置对比
- POST /device-configs/export-diff: 导出差异为HTML
- POST /device-configs/preview-rollback: 预览配置回滚
- POST /device-configs/rollback: 执行配置回滚
- POST /device-configs/batch-rollback: 批量配置回滚

### 设备管理 (devices.py)
- GET /devices: 获取设备列表
- GET /devices/{device_id}: 获取设备详情
- POST /devices: 创建设备
- PUT /devices/{device_id}: 更新设备
- DELETE /devices/{device_id}: 删除设备
- POST /devices/batch: 批量创建设备
- PUT /devices/batch: 批量更新设备
- DELETE /devices/batch: 批量删除设备

⚠️ **注意**：设备连接测试功能已迁移到 `/device-connection` 模块

### 导入导出 (import_export.py)
- GET /import-export/template: 生成设备导入模板
- POST /import-export/import: 导入设备数据
- GET /import-export/export: 导出设备数据

### 通用查询 (universal_query.py)
- POST /universal-query/template: 执行基于模板的查询
- POST /universal-query/template-type: 执行基于模板类型的查询
- POST /universal-query/template/{template_id}/commands/preview: 预览模板命令
- POST /universal-query/template/{template_id}/parameters/validate: 验证模板参数
- GET /universal-query/stats: 获取查询引擎统计信息
- GET /universal-query/health: 查询引擎健康检查
- POST /universal-query/mac: MAC地址查询（便捷接口）
- POST /universal-query/interface-status: 接口状态查询（便捷接口）
- POST /universal-query/config: 配置显示查询（便捷接口）

#### 原网络查询功能（兼容接口，标记为废弃）
- POST /universal-query/legacy/execute: 执行网络查询（原network_query接口）
- POST /universal-query/legacy/execute-by-ip: 根据IP执行网络查询（原network_query接口）
- POST /universal-query/legacy/mac-query: MAC地址查询（原network_query接口，已废弃）
- POST /universal-query/legacy/interface-status: 接口状态查询（原network_query接口，已废弃）
- POST /universal-query/legacy/custom-commands: 执行自定义命令（原network_query接口）
- GET /universal-query/legacy/templates: 获取可用查询模板（原network_query接口）
- GET /universal-query/legacy/health: 网络查询服务健康检查（原network_query接口，已废弃）

### 操作日志 (operation_logs.py)
- GET /operation-logs: 获取操作日志列表
- GET /operation-logs/stats: 获取操作日志统计
- DELETE /operation-logs/cleanup: 清理操作日志

### 权限缓存 (permission_cache.py)
- GET /permission-cache/stats: 获取权限缓存统计
- POST /permission-cache/test-user: 测试用户权限缓存
- DELETE /permission-cache/user/{user_id}: 清除用户权限缓存
- DELETE /permission-cache/role/{role_id}: 清除角色权限缓存
- DELETE /permission-cache/all: 清除所有权限缓存

### 权限管理 (permissions.py)
- GET /permissions: 获取权限列表
- GET /permissions/{permission_id}: 获取权限详情
- POST /permissions: 创建权限
- PUT /permissions/{permission_id}: 更新权限
- DELETE /permissions/{permission_id}: 删除权限
- PUT /permissions/{permission_id}/status: 更新权限状态
- POST /permissions/batch-create: 批量创建权限
- PUT /permissions/batch-update: 批量更新权限
- DELETE /permissions/batch-delete: 批量删除权限

### 查询历史 (query_history.py)
- GET /query-history: 获取查询历史列表
- GET /query-history/{history_id}: 获取查询历史详情
- POST /query-history: 创建查询历史
- DELETE /query-history/{history_id}: 删除查询历史
- POST /query-history/batch-create: 批量创建查询历史
- DELETE /query-history/batch-delete: 批量删除查询历史
- GET /query-history/recent: 获取最近查询历史
- GET /query-history/stats: 获取查询历史统计
- DELETE /query-history/cleanup: 清理旧查询历史

### 查询模板 (query_templates.py)
- GET /query-templates: 获取查询模板列表
- GET /query-templates/{template_id}: 获取查询模板详情
- POST /query-templates: 创建查询模板
- PUT /query-templates/{template_id}: 更新查询模板
- DELETE /query-templates/{template_id}: 删除查询模板
- POST /query-templates/batch: 批量创建查询模板
- PUT /query-templates/batch: 批量更新查询模板
- DELETE /query-templates/batch: 批量删除查询模板
- PUT /query-templates/{template_id}/activate: 激活查询模板
- PUT /query-templates/{template_id}/deactivate: 停用查询模板
- PUT /query-templates/batch/activate: 批量激活/停用查询模板
- GET /query-templates/active: 获取所有激活的查询模板
- GET /query-templates/type/{template_type}: 根据类型获取查询模板
- GET /query-templates/with-commands: 获取包含厂商命令的查询模板

### 基地管理 (regions.py)
- GET /regions: 获取基地列表
- GET /regions/{region_id}: 获取基地详情
- POST /regions: 创建基地
- PUT /regions/{region_id}: 更新基地
- DELETE /regions/{region_id}: 删除基地
- POST /regions/batch: 批量创建基地
- PUT /regions/batch: 批量更新基地
- DELETE /regions/batch: 批量删除基地
- GET /regions/code/{region_code}: 根据代码获取基地

### 角色管理 (roles.py)
- GET /roles: 获取角色列表
- GET /roles/{role_id}: 获取角色详情
- POST /roles: 创建角色
- PUT /roles/{role_id}: 更新角色
- DELETE /roles/{role_id}: 删除角色
- PUT /roles/{role_id}/status: 更新角色状态
- POST /roles/{role_id}/permissions: 分配角色权限
- POST /roles/{role_id}/permissions/add: 为角色添加权限
- DELETE /roles/{role_id}/permissions/remove: 移除角色权限
- GET /roles/{role_id}/permissions: 获取角色权限列表
- POST /roles/batch: 批量创建角色
- PUT /roles/batch: 批量更新角色
- DELETE /roles/batch: 批量删除角色

---

## 📋 快速查找索引

### 按功能分类
- **认证与权限**: `/auth/*`, `/permissions/*`, `/roles/*`, `/user-relations/*`
- **设备管理**: `/devices/*`, `/device-connection/*`, `/device-configs/*`
- **查询功能**: `/universal-query/*`, `/query-templates/*`, `/query-history/*`
- **系统管理**: `/stats/*`, `/operation-logs/*`, `/permission-cache/*`, `/admin/*`
- **数据管理**: `/import-export/*`, `/vendors/*`, `/regions/*`, `/vendor-commands/*`
- **用户界面**: `/web/*`, `/cli/*`

### 按HTTP方法分类
- **GET**: 查询数据、获取信息、导出功能
- **POST**: 创建资源、执行操作、批量处理
- **PUT**: 更新资源、修改状态
- **DELETE**: 删除资源、清理操作
- **WebSocket**: 实时通信（CLI终端）

### 常用接口快速导航
- **系统状态**: `GET /health`, `GET /stats/*`
- **用户登录**: `POST /auth/login`
- **设备测试**: `POST /device-connection/test`
- **设备查询**: `POST /universal-query/mac`, `POST /universal-query/interface-status`
- **CLI终端**: `WS /cli/connect/{device_id}`
- **配置管理**: `GET /device-configs`, `POST /device-configs/compare`

---

**完整更新时间**: 2025-08-01  
**API版本**: v1.0 (统一重构版)  
**主要优化**: 统计功能统一、接口架构清晰、文档结构优化