"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: __init__.py
@DateTime: 2025/07/23
@Docs: DAO层统一导出
"""

from app.dao.base import BaseDAO
from app.dao.device import DeviceDAO
from app.dao.device_config import DeviceConfigDAO
from app.dao.operation_log import OperationLogDAO
from app.dao.permission import PermissionDAO
from app.dao.query_history import QueryHistoryDAO
from app.dao.query_template import QueryTemplateDAO
from app.dao.region import RegionDAO
from app.dao.role import RoleDAO
from app.dao.user import UserDAO
from app.dao.vendor import VendorDAO
from app.dao.vendor_command import VendorCommandDAO

__all__ = [
    "BaseDAO",
    "UserDAO",
    "RoleDAO",
    "PermissionDAO",
    "OperationLogDAO",
    "DeviceDAO",
    "RegionDAO",
    "DeviceConfigDAO",
    "QueryTemplateDAO",
    "VendorCommandDAO",
    "QueryHistoryDAO",
    "VendorDAO",
]
