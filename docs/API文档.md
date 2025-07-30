# AutoNetwork API 文档

## 基础 URL：`http://localhost:8000/api`
## 版本前缀：`/v1`

## 接口列表

### 后台管理仪表板 (admin_dashboard.py)
- GET /admin-dashboard/stats: 获取统计数据
- GET /admin-dashboard/user-permissions: 检查用户权限
- GET /admin-dashboard/user-permissions/inheritance: 获取用户权限继承关系
- POST /admin-dashboard/users/batch-enable: 批量启用用户
- POST /admin-dashboard/users/batch-disable: 批量禁用用户
- GET /admin-dashboard/export/users: 导出用户数据
- GET /admin-dashboard/export/roles: 导出角色数据

### 设备认证 (authentication.py)
- GET /authentication/credentials: 获取设备认证凭据
- POST /authentication/test: 测试设备认证
- POST /authentication/batch-test: 批量测试设备认证
- POST /authentication/dynamic-username: 生成动态用户名
- DELETE /authentication/dynamic-password/cache: 清除动态密码缓存
- GET /authentication/dynamic-password/cache: 获取动态密码缓存信息
- GET /authentication/config: 获取认证配置信息

### CLI 终端 (cli_terminal.py)
- WS /cli-terminal/connect/{device_id}: 连接设备CLI终端
- WS /cli-terminal/manual-connect: 连接手动配置设备CLI终端
- GET /cli-terminal/sessions: 获取当前用户的所有CLI会话
- GET /cli-terminal/all-sessions: 获取所有CLI会话（管理员）
- GET /cli-terminal/stats: 获取CLI会话统计信息
- DELETE /cli-terminal/session/{session_id}: 关闭指定的CLI会话
- GET /cli-terminal/platforms: 获取支持的设备平台列表
- POST /cli-terminal/validate-config: 验证设备连接配置
- GET /cli-terminal/session/{session_id}: 获取指定会话的详细信息
- POST /cli-terminal/session/{session_id}/reconnect: 重连指定的CLI会话

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

### 设备连接 (device_connection.py)
- POST /device-connection/test/{device_id}: 测试单个设备连接
- POST /device-connection/batch-test: 批量测试设备连接
- POST /device-connection/stability-test/{device_id}: 测试设备连接稳定性
- GET /device-connection/credentials/{device_id}: 获取设备认证凭据
- POST /device-connection/validate-credentials: 验证设备认证凭据
- POST /device-connection/encrypt-password: 加密设备密码
- GET /device-connection/pool-stats: 获取连接池统计信息
- GET /device-connection/manager-stats: 获取连接管理器统计信息
- POST /device-connection/cleanup-idle: 清理空闲连接
- DELETE /device-connection/close/{device_id}: 关闭设备连接
- POST /device-connection/pool/start: 启动连接池
- POST /device-connection/pool/stop: 停止连接池
- POST /device-connection/batch-test-by-condition: 根据条件批量测试设备
- DELETE /device-connection/dynamic-password/cache: 清除动态密码缓存
- GET /device-connection/dynamic-password/cache: 获取缓存密码信息
- GET /device-connection/test-stats: 获取测试统计信息

### 设备管理 (devices.py)
- GET /devices: 获取设备列表
- GET /devices/{device_id}: 获取设备详情
- POST /devices: 创建设备
- PUT /devices/{device_id}: 更新设备
- DELETE /devices/{device_id}: 删除设备
- POST /devices/batch-create: 批量创建设备
- PUT /devices/batch-update: 批量更新设备
- DELETE /devices/batch-delete: 批量删除设备
- POST /devices/test-connection/{device_id}: 测试设备连接

### 导入导出 (import_export.py)
- GET /import-export/template: 生成设备导入模板
- POST /import-export/import: 导入设备数据
- GET /import-export/export: 导出设备数据

### 网络查询 (network_query.py)
- POST /network-query/execute: 执行网络查询
- POST /network-query/mac: MAC地址查询
- POST /network-query/interface-status: 接口状态查询
- POST /network-query/custom-command: 执行自定义命令
- GET /network-query/templates: 获取可用查询模板

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

### 通用查询 (universal_query.py)
- POST /universal-query/template: 执行基于模板的查询
- POST /universal-query/template-type: 执行基于模板类型的查询
- POST /universal-query/template/{template_id}/commands/preview: 预览模板命令
- POST /universal-query/template/{template_id}/parameters/validate: 验证模板参数
- GET /universal-query/stats: 获取查询引擎统计信息
- GET /universal-query/health: 查询引擎健康检查
- POST /universal-query/mac: MAC地址查询
- POST /universal-query/interface-status: 接口状态查询
- POST /universal-query/config: 配置显示查询

### 用户关系 (user_relations.py)
- POST /user-relations/batch/users/roles/assign: 批量分配用户角色
- POST /user-relations/batch/users/roles/add: 批量添加用户角色
- DELETE /user-relations/batch/users/roles/remove: 批量移除用户角色
- POST /user-relations/batch/users/permissions/assign: 批量分配用户权限
- GET /user-relations/roles/{role_id}/users: 获取角色下的所有用户
- GET /user-relations/permissions/{permission_id}/users: 获取权限下的所有用户
- GET /user-relations/users/{user_id}/summary: 获取用户权限汇总
- POST /user-relations/roles/{role_id}/users/assign: 为角色批量分配用户
- DELETE /user-relations/roles/{role_id}/users/remove: 从角色批量移除用户

### 用户管理 (users.py)
- GET /users: 获取用户列表
- GET /users/{user_id}: 获取用户详情
- POST /users: 创建用户
- PUT /users/{user_id}: 更新用户
- DELETE /users/{user_id}: 删除用户
- PUT /users/{user_id}/status: 更新用户状态
- POST /users/{user_id}/roles: 分配用户角色
- POST /users/{user_id}/roles/add: 为用户添加角色
- DELETE /users/{user_id}/roles/remove: 移除用户角色
- GET /users/{user_id}/roles: 获取用户角色列表
- POST /users/{user_id}/permissions: 设置用户权限
- POST /users/{user_id}/permissions/add: 为用户添加权限
- DELETE /users/{user_id}/permissions/remove: 移除用户权限
- GET /users/{user_id}/permissions: 获取用户权限列表
- POST /users/batch: 批量创建用户
- PUT /users/batch: 批量更新用户
- DELETE /users/batch: 批量删除用户

### 厂商命令 (vendor_commands.py)
- GET /vendor-commands: 获取厂商命令列表
- GET /vendor-commands/{command_id}: 获取厂商命令详情
- POST /vendor-commands: 创建厂商命令
- PUT /vendor-commands/{command_id}: 更新厂商命令
- DELETE /vendor-commands/{command_id}: 删除厂商命令
- POST /vendor-commands/batch: 批量创建厂商命令
- PUT /vendor-commands/batch/status: 批量更新命令状态
- DELETE /vendor-commands/batch: 批量删除厂商命令
- GET /vendor-commands/statistics/overview: 获取厂商命令统计信息

### 厂商管理 (vendors.py)
- GET /vendors: 获取厂商列表
- GET /vendors/{vendor_id}: 获取厂商详情
- POST /vendors: 创建厂商
- PUT /vendors/{vendor_id}: 更新厂商
- DELETE /vendors/{vendor_id}: 删除厂商
- POST /vendors/batch: 批量创建厂商
- PUT /vendors/batch: 批量更新厂商
- DELETE /vendors/batch: 批量删除厂商
- GET /vendors/code/{vendor_code}: 根据代码获取厂商

### Web 路由 (web_routes.py)
- GET /web/cli-terminal: 获取CLI终端页面
- GET /web/cli-terminal-simple: 获取简化版CLI终端页面
- GET /web/cli-terminal-test: 获取无需认证的CLI终端测试页面

### 系统路由
- GET /: 根路由
- GET /health: 健康检查接口
- GET /metrics: 获取应用监控指标