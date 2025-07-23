"""
-*- coding: utf-8 -*-
 @Author: li
 @Email: lijianqiao2906@live.com
 @FileName: __init__.py
 @DateTime: 2025/3/11 上午9:53
 @Docs: Schemas包导出
"""

# 基础schemas
# 认证schemas
from app.schemas.auth import *  # noqa: F403
from app.schemas.base import *  # noqa: F403

# 网络自动化schemas
from app.schemas.device import *  # noqa: F403
from app.schemas.device_config import *  # noqa: F403
from app.schemas.network_query import *  # noqa: F403

# 操作日志schemas
from app.schemas.operation_log import *  # noqa: F403

# 权限管理schemas
from app.schemas.permission import *  # noqa: F403
from app.schemas.query_history import *  # noqa: F403
from app.schemas.query_template import *  # noqa: F403
from app.schemas.region import *  # noqa: F403

# 角色管理schemas
from app.schemas.role import *  # noqa: F403

# 类型schemas
from app.schemas.types import *  # noqa: F403

# 用户管理schemas
from app.schemas.user import *  # noqa: F403
from app.schemas.vendor import *  # noqa: F403
from app.schemas.vendor_command import *  # noqa: F403
