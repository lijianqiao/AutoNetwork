# CLI终端HTML模板使用说明

## 📖 概述

这是基于原生HTML、CSS和JavaScript实现的CLI终端界面，集成了Xterm.js终端模拟器，提供类似CRT的网络设备CLI体验。

## 🚀 功能特性

### ✅ 已实现功能

- **多终端标签页** - 同时管理多个终端会话
- **双连接模式** - 支持数据库设备选择和手动IP配置
- **实时WebSocket通信** - 真实的CLI交互体验
- **会话管理** - 查看和管理所有活跃会话
- **响应式设计** - 支持桌面和移动端
- **键盘快捷键** - 丰富的快捷键支持
- **权限集成** - 完整的RBAC权限验证

### 🎮 快捷键支持

- `Ctrl + T` - 新建终端
- `Ctrl + W` - 关闭当前终端
- `Ctrl + 1-9` - 切换到指定终端
- `Ctrl + L` - 清屏
- `Ctrl + C` - 中断命令

## 📁 文件结构

```
templates/
├── cli_terminal.html          # 主要的CLI终端页面
└── README.md                 # 使用说明文档

app/api/v1/
├── web_routes.py             # Web页面路由
├── cli_terminal.py           # CLI终端API接口
└── __init__.py               # 路由注册
```

## 🔧 访问方式

### 1. 直接访问HTML页面

```
http://localhost:8000/api/v1/web/cli-terminal
```

### 2. API接口

- **WebSocket终端连接**：
  - 数据库设备：`ws://localhost:8000/api/v1/cli/terminal/device/{device_id}`
  - 手动配置：`ws://localhost:8000/api/v1/cli/terminal/manual`

- **REST API接口**：
  - 获取用户会话：`GET /api/v1/cli/sessions`
  - 获取会话统计：`GET /api/v1/cli/sessions/stats`
  - 获取支持平台：`GET /api/v1/cli/platforms`
  - 关闭会话：`DELETE /api/v1/cli/sessions/{session_id}`

## 🎯 使用流程

### 1. 访问页面
```bash
# 启动应用
uv run python start.py

# 访问CLI终端页面
http://localhost:8000/api/v1/web/cli-terminal
```

### 2. 连接设备

#### 选择数据库设备
1. 点击"新建终端"按钮
2. 选择"选择设备"标签
3. 从下拉列表中选择设备
4. 如果是动态认证，输入密码
5. 点击"连接设备"

#### 手动配置设备
1. 点击"新建终端"按钮
2. 选择"手动配置"标签
3. 填写设备IP、用户名、密码等信息
4. 选择设备平台类型
5. 点击"连接设备"

### 3. 使用终端

连接成功后，可以：
- 直接输入命令进行交互
- 使用Tab键进行命令补全
- 使用↑/↓键查看命令历史
- 使用Ctrl+C中断命令执行
- 使用工具栏按钮进行重连、清屏等操作

### 4. 会话管理

- 点击"会话管理"查看所有活跃会话
- 查看会话统计信息
- 关闭不需要的会话

## 🔐 权限要求

访问CLI终端需要以下权限：

- `cli:access` - CLI终端访问权限（必需）
- `cli:execute` - CLI命令执行权限
- `cli:config` - CLI配置命令权限

## 🎨 界面定制

### 修改终端主题

在`cli_terminal.html`中找到Xterm终端初始化代码，修改theme配置：

```javascript
const xterm = new Terminal({
    theme: {
        foreground: '#ffffff',    // 前景色
        background: '#1e1e1e',    // 背景色
        cursor: '#ffffff',        // 光标颜色
        // ... 其他颜色配置
    }
});
```

### 修改页面样式

直接编辑`cli_terminal.html`中的CSS样式部分，可以自定义：

- 页面布局和配色
- 按钮样式
- 表格样式
- 响应式断点

## 🔍 故障排除

### 常见问题

1. **页面无法访问**
   - 检查服务是否正常启动
   - 确认路由注册是否正确
   - 检查权限是否配置

2. **WebSocket连接失败**
   - 检查网络连接
   - 确认WebSocket端点URL正确
   - 检查防火墙设置

3. **设备连接超时**
   - 检查设备IP地址和端口
   - 确认设备SSH服务正常
   - 检查认证信息是否正确

4. **权限被拒绝**
   - 确认用户具有CLI相关权限
   - 检查JWT token是否有效
   - 联系管理员分配权限

### 调试模式

打开浏览器开发者工具，查看Console输出：

```javascript
// 查看WebSocket连接状态
console.log('WebSocket状态:', websocket.readyState);

// 查看终端实例
console.log('终端实例:', terminals);

// 查看当前活跃终端
console.log('活跃终端:', activeTerminalId);
```

## 🌐 浏览器兼容性

支持的浏览器：
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## 📈 性能优化建议

1. **连接数限制** - 建议单用户最多创建10个并发终端
2. **会话清理** - 定期关闭不使用的会话
3. **网络优化** - 在网络延迟较高的环境中适当增加超时时间

## 🔄 更新日志

### v1.0.0 (2025-07-30)
- ✨ 完整的原生HTML CLI终端实现
- 🎯 支持多终端标签页管理
- 🔐 集成RBAC权限系统
- 📱 响应式设计，支持移动端
- ⚡ 高性能WebSocket通信
- 🎨 现代化UI设计

## 📧 技术支持

如有问题或建议，请联系：lijianqiao2906@live.com

## 📄 许可证

MIT License