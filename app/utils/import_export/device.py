"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: device.py
@DateTime: 2025/07/23
@Docs: 设备导入导出服务
"""

import re
from typing import Any

import pandas as pd

from app.core.exceptions import BusinessException
from app.dao.device import DeviceDAO
from app.dao.region import RegionDAO
from app.dao.vendor import VendorDAO
from app.models.device import Device
from app.models.region import Region
from app.models.vendor import Vendor
from app.services.device import DeviceService
from app.utils.deps import OperationContext
from app.utils.import_export.base import (
    BaseImportExportService,
    FieldMapping,
    ImportExportConfig,
)
from app.utils.logger import logger


class DeviceImportExportService(BaseImportExportService):
    """设备导入导出服务"""

    def __init__(self):
        config = ImportExportConfig(
            model_name="device",
            display_name="网络设备",
            sheet_name="设备列表",
            main_fields=[
                FieldMapping(
                    field_name="hostname",
                    display_name="设备主机名",
                    english_name="hostname",
                    is_required=True,
                    field_type="str",
                    max_length=100,
                    min_length=2,
                    description="设备的主机名，在系统中必须唯一",
                    example_value="SW-CD-01",
                ),
                FieldMapping(
                    field_name="ip_address",
                    display_name="管理IP地址",
                    english_name="ip_address",
                    is_required=True,
                    field_type="str",
                    max_length=45,
                    min_length=7,
                    description="设备的管理IP地址，支持IPv4和IPv6",
                    example_value="192.168.1.100",
                ),
                FieldMapping(
                    field_name="device_type",
                    display_name="设备类型",
                    english_name="device_type",
                    is_required=True,
                    field_type="str",
                    max_length=50,
                    description="设备类型",
                    example_value="switch",
                    choices=["switch", "router", "firewall"],
                ),
                FieldMapping(
                    field_name="network_layer",
                    display_name="网络层级",
                    english_name="network_layer",
                    is_required=True,
                    field_type="str",
                    max_length=50,
                    description="网络层级架构",
                    example_value="access",
                    choices=["access", "aggregation", "core"],
                ),
                FieldMapping(
                    field_name="model",
                    display_name="设备型号",
                    english_name="model",
                    is_required=True,
                    field_type="str",
                    max_length=100,
                    description="设备的具体型号",
                    example_value="S5130-28S-HPWR-EI",
                ),
                FieldMapping(
                    field_name="serial_number",
                    display_name="序列号",
                    english_name="serial_number",
                    is_required=True,
                    field_type="str",
                    max_length=100,
                    description="设备的序列号",
                    example_value="210235A1ABC123456789",
                ),
                FieldMapping(
                    field_name="location",
                    display_name="物理位置",
                    english_name="location",
                    is_required=True,
                    field_type="str",
                    max_length=200,
                    description="设备的物理位置描述",
                    example_value="机房A-机柜01-U1-U2",
                ),
                FieldMapping(
                    field_name="auth_type",
                    display_name="认证类型",
                    english_name="auth_type",
                    is_required=True,
                    field_type="str",
                    description="设备认证方式",
                    example_value="dynamic",
                    choices=["dynamic", "static"],
                ),
                FieldMapping(
                    field_name="static_username",
                    display_name="静态用户名",
                    english_name="static_username",
                    is_required=False,
                    field_type="str",
                    max_length=200,
                    description="静态认证时的用户名，认证类型为static时必填",
                    example_value="admin",
                ),
                FieldMapping(
                    field_name="static_password",
                    display_name="静态密码",
                    english_name="static_password",
                    is_required=False,
                    field_type="str",
                    max_length=200,
                    description="静态认证时的密码，认证类型为static时必填",
                    example_value="password123",
                ),
                FieldMapping(
                    field_name="ssh_port",
                    display_name="SSH端口",
                    english_name="ssh_port",
                    is_required=False,
                    field_type="int",
                    default_value=22,
                    description="SSH连接端口，默认22",
                    example_value="22",
                ),
                FieldMapping(
                    field_name="is_active",
                    display_name="是否在用",
                    english_name="is_active",
                    is_required=False,
                    field_type="bool",
                    default_value=True,
                    description="设备是否在使用中",
                    example_value="是",
                    choices=["是", "否"],
                ),
            ],
            foreign_key_fields=[
                # 厂商相关字段
                FieldMapping(
                    field_name="vendor_code",
                    display_name="厂商代码",
                    english_name="vendor_code",
                    is_required=True,
                    field_type="str",
                    max_length=50,
                    description="厂商代码，如不存在会自动创建厂商",
                    example_value="h3c",
                ),
                FieldMapping(
                    field_name="vendor_name",
                    display_name="厂商名称",
                    english_name="vendor_name",
                    is_required=True,
                    field_type="str",
                    max_length=100,
                    description="厂商名称，创建新厂商时必填",
                    example_value="华三",
                ),
                FieldMapping(
                    field_name="scrapli_platform",
                    display_name="Scrapli平台标识",
                    english_name="scrapli_platform",
                    is_required=True,
                    field_type="str",
                    max_length=100,
                    description="Scrapli连接平台标识，创建新厂商时必填",
                    example_value="hp_comware",
                ),
                FieldMapping(
                    field_name="default_ssh_port",
                    display_name="厂商默认SSH端口",
                    english_name="default_ssh_port",
                    is_required=False,
                    field_type="int",
                    default_value=22,
                    description="厂商默认SSH端口，创建新厂商时使用",
                    example_value="22",
                ),
                FieldMapping(
                    field_name="connection_timeout",
                    display_name="厂商连接超时",
                    english_name="connection_timeout",
                    is_required=False,
                    field_type="int",
                    default_value=30,
                    description="厂商连接超时时间（秒），创建新厂商时使用",
                    example_value="30",
                ),
                FieldMapping(
                    field_name="command_timeout",
                    display_name="厂商命令超时",
                    english_name="command_timeout",
                    is_required=False,
                    field_type="int",
                    default_value=10,
                    description="厂商命令超时时间（秒），创建新厂商时使用",
                    example_value="10",
                ),
                # 基地相关字段
                FieldMapping(
                    field_name="region_code",
                    display_name="基地代码",
                    english_name="region_code",
                    is_required=True,
                    field_type="str",
                    max_length=50,
                    description="基地代码，如不存在会自动创建基地",
                    example_value="cd",
                ),
                FieldMapping(
                    field_name="region_name",
                    display_name="基地名称",
                    english_name="region_name",
                    is_required=True,
                    field_type="str",
                    max_length=100,
                    description="基地名称，创建新基地时必填",
                    example_value="成都",
                ),
                FieldMapping(
                    field_name="snmp_community",
                    display_name="SNMP社区字符串",
                    english_name="snmp_community",
                    is_required=True,
                    field_type="str",
                    max_length=200,
                    description="SNMP社区字符串，创建新基地时必填",
                    example_value="public",
                ),
                FieldMapping(
                    field_name="region_description",
                    display_name="基地描述",
                    english_name="region_description",
                    is_required=False,
                    field_type="str",
                    description="基地描述，创建新基地时使用",
                    example_value="成都研发中心",
                ),
            ],
            unique_fields=["hostname", "ip_address"],
            update_fields=[
                "model",
                "serial_number",
                "location",
                "auth_type",
                "static_username",
                "static_password",
                "ssh_port",
                "is_active",
            ],
        )
        super().__init__(config)
        self.device_dao = DeviceDAO()
        self.vendor_dao = VendorDAO()
        self.region_dao = RegionDAO()
        self.device_service = DeviceService()

    async def _get_example_data(self) -> list[list[str]]:
        """获取示例数据"""
        return [
            [
                "SW-CD-01",
                "192.168.1.100",
                "switch",
                "access",
                "S5130-28S-HPWR-EI",
                "210235A1ABC123456789",
                "机房A-机柜01-U1-U2",
                "dynamic",
                "",
                "",
                "22",
                "是",
                "h3c",
                "华三",
                "hp_comware",
                "22",
                "30",
                "10",
                "cd",
                "成都",
                "public",
                "成都研发中心",
            ],
            [
                "SW-WX-02",
                "192.168.2.100",
                "switch",
                "aggregation",
                "S6520X-54QS-EI",
                "210235A2ABC123456790",
                "机房B-机柜02-U3-U4",
                "static",
                "admin",
                "password123",
                "22",
                "是",
                "huawei",
                "华为",
                "huawei_vrp",
                "22",
                "30",
                "10",
                "wx",
                "无锡",
                "private",
                "无锡生产基地",
            ],
        ]

    async def _convert_model_to_export_row(self, model: Device) -> list[str]:
        """将设备模型转换为导出行数据"""
        try:
            # 加载关联对象
            await model.fetch_related("vendor", "region")

            return [
                model.hostname,
                model.ip_address,
                model.device_type,
                model.network_layer,
                model.model,
                model.serial_number,
                model.location,
                model.auth_type,
                model.static_username or "",
                model.static_password or "",
                str(model.ssh_port),
                "是" if model.is_active else "否",
                model.vendor.vendor_code,
                model.vendor.vendor_name,
                model.vendor.scrapli_platform,
                str(model.vendor.default_ssh_port),
                str(model.vendor.connection_timeout),
                str(model.vendor.command_timeout),
                model.region.region_code,
                model.region.region_name,
                model.region.snmp_community,
                model.region.description or "",
            ]
        except Exception as e:
            logger.error(f"转换设备模型失败: {e}")
            raise BusinessException(f"转换设备模型失败: {e}") from e

    async def _validate_row_fields(self, row: dict[str, Any], row_number: int) -> list[str]:
        """验证行字段格式"""
        errors = []

        # IP地址格式验证
        ip_address = row.get("管理IP地址")
        if ip_address and not self._is_valid_ip(str(ip_address)):
            errors.append(f"第{row_number}行：管理IP地址格式不正确")

        # 设备类型验证
        device_type = row.get("设备类型")
        if device_type and device_type not in ["switch", "router", "firewall"]:
            errors.append(f"第{row_number}行：设备类型必须为 switch、router 或 firewall")

        # 网络层级验证
        network_layer = row.get("网络层级")
        if network_layer and network_layer not in ["access", "aggregation", "core"]:
            errors.append(f"第{row_number}行：网络层级必须为 access、aggregation 或 core")

        # 认证类型验证
        auth_type = row.get("认证类型")
        if auth_type and auth_type not in ["dynamic", "static"]:
            errors.append(f"第{row_number}行：认证类型必须为 dynamic 或 static")

        # 静态认证字段验证
        if auth_type == "static":
            static_username = row.get("静态用户名")
            static_password = row.get("静态密码")
            if not static_username or pd.isna(static_username) or str(static_username).strip() == "":
                errors.append(f"第{row_number}行：认证类型为static时，静态用户名为必填")
            if not static_password or pd.isna(static_password) or str(static_password).strip() == "":
                errors.append(f"第{row_number}行：认证类型为static时，静态密码为必填")

        # SSH端口验证
        ssh_port = row.get("SSH端口")
        if ssh_port and not self._is_valid_port(ssh_port):
            errors.append(f"第{row_number}行：SSH端口必须为1-65535之间的数字")

        # 是否在用验证
        is_active = row.get("是否在用")
        if is_active and str(is_active) not in ["是", "否", "True", "False", "true", "false", "1", "0"]:
            errors.append(f"第{row_number}行：是否在用必须为 是/否")

        # 厂商超时字段验证
        for _field_name, display_name in [
            ("厂商默认SSH端口", "厂商默认SSH端口"),
            ("厂商连接超时", "厂商连接超时"),
            ("厂商命令超时", "厂商命令超时"),
        ]:
            value = row.get(display_name)
            if value and not self._is_valid_number(value):
                errors.append(f"第{row_number}行：{display_name}必须为数字")

        return errors

    def _is_valid_ip(self, ip: str) -> bool:
        """验证IP地址格式"""
        ipv4_pattern = r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
        ipv6_pattern = r"^(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$|^::1$|^::$"
        return bool(re.match(ipv4_pattern, ip.strip()) or re.match(ipv6_pattern, ip.strip()))

    def _is_valid_port(self, port: Any) -> bool:
        """验证端口号"""
        try:
            port_num = int(port)
            return 1 <= port_num <= 65535
        except (ValueError, TypeError):
            return False

    def _is_valid_number(self, value: Any) -> bool:
        """验证是否为数字"""
        try:
            int(value)
            return True
        except (ValueError, TypeError):
            return False

    async def _convert_import_data(self, data: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """转换导入数据格式"""
        converted_data = []

        for row in data:
            # 基本字段转换
            converted_row = {
                "hostname": self._safe_str_convert(row.get("设备主机名")),
                "ip_address": self._safe_str_convert(row.get("管理IP地址")),
                "device_type": self._safe_str_convert(row.get("设备类型")),
                "network_layer": self._safe_str_convert(row.get("网络层级")),
                "model": self._safe_str_convert(row.get("设备型号")),
                "serial_number": self._safe_str_convert(row.get("序列号")),
                "location": self._safe_str_convert(row.get("物理位置")),
                "auth_type": self._safe_str_convert(row.get("认证类型")),
                "static_username": self._safe_str_convert(row.get("静态用户名"), allow_empty=True),
                "static_password": self._safe_str_convert(row.get("静态密码"), allow_empty=True),
                "ssh_port": self._safe_int_convert(row.get("SSH端口"), default=22),
            }

            # 是否在用字段转换
            is_active_value = self._safe_str_convert(row.get("是否在用"), default="是")
            converted_row["is_active"] = is_active_value in ["是", "True", "true", "1"]

            # 厂商字段
            converted_row["vendor_data"] = {
                "vendor_code": self._safe_str_convert(row.get("厂商代码")),
                "vendor_name": self._safe_str_convert(row.get("厂商名称")),
                "scrapli_platform": self._safe_str_convert(row.get("Scrapli平台标识")),
                "default_ssh_port": self._safe_int_convert(row.get("厂商默认SSH端口"), default=22),
                "connection_timeout": self._safe_int_convert(row.get("厂商连接超时"), default=30),
                "command_timeout": self._safe_int_convert(row.get("厂商命令超时"), default=10),
            }

            # 基地字段
            converted_row["region_data"] = {
                "region_code": self._safe_str_convert(row.get("基地代码")),
                "region_name": self._safe_str_convert(row.get("基地名称")),
                "snmp_community": self._safe_str_convert(row.get("SNMP社区字符串")),
                "description": self._safe_str_convert(row.get("基地描述"), allow_empty=True),
            }

            converted_data.append(converted_row)

        return converted_data

    async def _import_validated_data(
        self, data: list[dict[str, Any]], operation_context: OperationContext, update_existing: bool
    ) -> dict[str, Any]:
        """导入验证通过的数据"""
        success_count = 0
        error_count = 0
        errors = []
        imported_ids = []

        for i, row_data in enumerate(data, 1):
            try:
                # 处理厂商
                vendor = await self._get_or_create_vendor(row_data["vendor_data"])

                # 处理基地
                region = await self._get_or_create_region(row_data["region_data"])

                # 准备设备数据
                device_data = {
                    "hostname": row_data["hostname"],
                    "ip_address": row_data["ip_address"],
                    "device_type": row_data["device_type"],
                    "network_layer": row_data["network_layer"],
                    "vendor_id": vendor.id,
                    "region_id": region.id,
                    "model": row_data["model"],
                    "serial_number": row_data["serial_number"],
                    "location": row_data["location"],
                    "auth_type": row_data["auth_type"],
                    "static_username": row_data["static_username"],
                    "static_password": row_data["static_password"],
                    "ssh_port": row_data["ssh_port"],
                    "is_active": row_data["is_active"],
                }

                # 检查是否存在
                existing_device = None
                for unique_field in self.config.unique_fields:
                    if unique_field in device_data:
                        existing_device = await self._find_existing_device(unique_field, device_data[unique_field])
                        if existing_device:
                            break

                if existing_device and update_existing:
                    # 更新现有设备
                    update_data = {k: v for k, v in device_data.items() if k in self.config.update_fields}
                    update_data["version"] = existing_device.version

                    # 创建DeviceUpdateRequest对象
                    from app.schemas.device import DeviceUpdateRequest

                    update_request = DeviceUpdateRequest(**update_data)
                    updated_device = await self.device_service.update_device(
                        existing_device.id, update_request, operation_context
                    )
                    if not updated_device.data:
                        raise BusinessException(f"更新设备失败: {device_data['hostname']}")
                    imported_ids.append(str(updated_device.data.id))
                    success_count += 1
                    logger.info(f"更新设备: {device_data['hostname']}")

                elif not existing_device:
                    # 创建新设备
                    # 创建DeviceCreateRequest对象
                    from app.schemas.device import DeviceCreateRequest

                    create_request = DeviceCreateRequest(**device_data)
                    new_device = await self.device_service.create_device(create_request, operation_context)
                    if not new_device.data:
                        raise BusinessException(f"创建设备失败: {device_data['hostname']}")
                    imported_ids.append(str(new_device.data.id))
                    success_count += 1
                    logger.info(f"创建设备: {device_data['hostname']}")

                else:
                    # 设备已存在且不允许更新
                    errors.append(f"第{i}行：设备 {device_data['hostname']} 已存在")
                    error_count += 1

            except Exception as e:
                error_count += 1
                errors.append(f"第{i}行：导入失败 - {str(e)}")
                logger.error(f"导入第{i}行设备失败: {e}")

        return {
            "success_count": success_count,
            "error_count": error_count,
            "errors": errors,
            "imported_ids": imported_ids,
        }

    async def _get_or_create_vendor(self, vendor_data: dict[str, Any]) -> Vendor:
        """获取或创建厂商"""
        # 先查找现有厂商
        existing_vendor = await self.vendor_dao.get_by_vendor_code(vendor_data["vendor_code"])
        if existing_vendor:
            return existing_vendor

        # 创建新厂商
        new_vendor = await self.vendor_dao.create(**vendor_data)
        if not new_vendor:
            raise BusinessException(f"创建厂商失败: {vendor_data['vendor_name']}")
        logger.info(f"创建新厂商: {vendor_data['vendor_name']}")
        return new_vendor

    async def _get_or_create_region(self, region_data: dict[str, Any]) -> Region:
        """获取或创建基地"""
        # 先查找现有基地
        existing_region = await self.region_dao.get_by_region_code(region_data["region_code"])
        if existing_region:
            return existing_region

        # 创建新基地
        new_region = await self.region_dao.create(**region_data)
        if not new_region:
            raise BusinessException(f"创建基地失败: {region_data['region_name']}")
        logger.info(f"创建新基地: {region_data['region_name']}")
        return new_region

    async def _find_existing_device(self, field: str, value: Any) -> Device | None:
        """根据唯一字段查找现有设备"""
        try:
            if field == "hostname":
                return await self.device_dao.get_by_hostname(value)
            elif field == "ip_address":
                return await self.device_dao.get_by_ip_address(value)
            else:
                return None
        except Exception:
            return None
