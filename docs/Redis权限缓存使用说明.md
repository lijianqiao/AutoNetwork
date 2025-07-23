# Redis权限缓存系统使用说明

## 概述

本系统已将权限缓存从内存缓存升级为Redis缓存，提供更高性能和可扩展性的权限验证机制。

## 配置项

在 `.env` 文件中添加以下配置：

```env
# Redis配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0

# 权限缓存配置
PERMISSION_CACHE_TTL=600          # 权限缓存TTL，默认10分钟
ENABLE_REDIS_CACHE=true           # 是否启用Redis缓存
```

## 主要功能

### 1. 自动权限缓存
- 用户首次访问时，权限自动缓存到Redis
- 缓存键格式：`user:permissions:{user_id}`
- 默认TTL：10分钟（可配置）
- 支持集合类型权限数据

### 2. 智能缓存失效
- 用户权限变更时自动清除对应缓存
- 角色权限变更时清除所有相关用户缓存
- 支持装饰器自动缓存失效

### 3. 备用机制
- Redis不可用时自动降级为内存缓存
- 无缝切换，不影响业务功能

## API接口

### 缓存管理接口

```http
# 获取缓存统计
GET /api/v1/permission-cache/stats

# 清除用户权限缓存
DELETE /api/v1/permission-cache/user/{user_id}

# 清除角色权限缓存
DELETE /api/v1/permission-cache/role/{role_id}

# 清除所有权限缓存
DELETE /api/v1/permission-cache/all
```

## 使用方式

### 1. 在服务层使用缓存失效装饰器

```python
from app.utils.permission_cache_utils import invalidate_user_permission_cache

@invalidate_user_permission_cache("user_id")
async def assign_roles(self, user_id: UUID, role_ids: list[UUID]):
    """为用户分配角色，自动清除权限缓存"""
    # 业务逻辑
    pass
```

### 2. 手动管理缓存

```python
from app.utils.permission_cache_utils import (
    clear_user_permission_cache,
    clear_role_permission_cache,
    get_permission_cache_stats
)

# 清除用户权限缓存
await clear_user_permission_cache(user_id)

# 清除角色权限缓存
await clear_role_permission_cache(role_id)

# 获取缓存统计
stats = await get_permission_cache_stats()
```

### 3. 直接使用权限管理器

```python
from app.core.permissions.simple_decorators import permission_manager

# 清除用户缓存
await permission_manager.clear_user_cache(user_id)

# 清除角色缓存
await permission_manager.clear_role_cache(role_id)

# 获取缓存统计
stats = await permission_manager.get_cache_stats()
```

## 缓存策略

### 缓存键命名规范
- 用户权限：`user:permissions:{user_id}`
- 角色权限：`role:permissions:{role_id}`（预留）
- 系统缓存：`permission:cache:*`

### TTL策略
- 用户权限：默认10分钟
- 可通过配置项 `PERMISSION_CACHE_TTL` 调整
- 支持手动设置不同过期时间

### 失效策略
- 用户权限变更：立即清除该用户缓存
- 角色权限变更：清除所有用户权限缓存
- 系统维护：支持批量清除缓存

## 监控和运维

### 1. 启动时检查
- 系统启动时自动测试Redis连接
- 权限缓存系统初始化验证
- 自动降级机制验证

### 2. 运行时监控
- 缓存命中率统计
- Redis连接状态监控
- 内存使用情况跟踪

### 3. 日志记录
- 缓存操作日志
- 失效策略执行日志
- 错误和降级日志

## 测试

运行权限缓存测试：

```bash
# 测试Redis缓存功能
uv run python tests/test_permission_cache.py
```

## 性能优化

### 1. 连接池配置
- 使用Redis连接池避免频繁连接
- 支持连接超时和重试机制
- 连接保活配置

### 2. 序列化优化
- 使用pickle进行数据序列化
- 支持集合类型的高效存储
- 自动类型转换机制

### 3. 批量操作
- 支持模式匹配批量删除
- 批量设置和获取缓存
- 事务操作支持

## 故障排除

### 常见问题

1. **Redis连接失败**
   - 检查Redis服务是否启动
   - 验证连接配置是否正确
   - 查看网络连接状态

2. **权限缓存不生效**
   - 确认ENABLE_REDIS_CACHE配置
   - 检查TTL设置是否合理
   - 验证缓存失效逻辑

3. **性能问题**
   - 监控Redis内存使用
   - 检查缓存命中率
   - 优化TTL设置

### 日志查看

```bash
# 查看权限缓存相关日志
tail -f logs/sys_$(date +%Y-%m-%d).log | grep -i "permission\|cache\|redis"
```

## 最佳实践

1. **TTL设置**：根据业务特点调整缓存时间
2. **缓存预热**：系统启动时预加载常用权限
3. **监控告警**：设置Redis连接和缓存异常告警
4. **定期清理**：定期清理过期和无效缓存
5. **容量规划**：根据用户量规划Redis内存容量

## 升级说明

从内存缓存升级到Redis缓存的变更：

1. **新增依赖**：redis[hiredis]>=6.2.0
2. **新增配置**：权限缓存相关配置项
3. **新增接口**：权限缓存管理API
4. **兼容性**：保持向后兼容，支持降级机制
