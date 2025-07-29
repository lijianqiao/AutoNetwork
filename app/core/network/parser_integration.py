"""TextFSM解析器集成模块

@Author: li
@Email: lijianqiao2906@live.com
@FileName: parser_integration.py
@DateTime: 2025/01/27 10:30:00
@Docs: TextFSM解析器集成 - 将解析器集成到网络查询引擎中
"""

from typing import Any

from loguru import logger

from app.core.exceptions import BusinessException
from app.core.network.textfsm_parser import TextFSMParser
from app.models.device import Device
from app.schemas.network_query import NornirQueryResult
from app.schemas.types import ObjectUUID


class ParsedQueryResult:
    """解析后的查询结果"""

    def __init__(
        self,
        device_id: ObjectUUID | None,
        hostname: str,
        ip_address: str,
        command: str,
        success: bool,
        raw_output: str | None = None,
        parsed_data: list[dict[str, Any]] | None = None,
        error: str | None = None,
        execution_time: float = 0.0,
        template_used: str | None = None,
        parsing_method: str = "textfsm",
    ):
        self.device_id = device_id
        self.hostname = hostname
        self.ip_address = ip_address
        self.command = command
        self.success = success
        self.raw_output = raw_output
        self.parsed_data = parsed_data or []
        self.error = error
        self.execution_time = execution_time
        self.template_used = template_used
        self.parsing_method = parsing_method

    def to_dict(self) -> dict[str, Any]:
        """转换为字典格式"""
        return {
            "device_id": str(self.device_id) if self.device_id else None,
            "hostname": self.hostname,
            "ip_address": self.ip_address,
            "command": self.command,
            "success": self.success,
            "raw_output": self.raw_output,
            "parsed_data": self.parsed_data,
            "parsed_count": len(self.parsed_data),
            "error": self.error,
            "execution_time": self.execution_time,
            "template_used": self.template_used,
            "parsing_method": self.parsing_method,
        }


class QueryResultParser:
    """查询结果解析器 - 集成TextFSM解析功能"""

    def __init__(self):
        """初始化查询结果解析器"""
        self.textfsm_parser = TextFSMParser()

        # 平台映射 - 将Scrapli平台标识映射到TextFSM平台标识
        self.platform_mapping = {
            "cisco_iosxe": "cisco_ios",
            "cisco_ios": "cisco_ios",
            "cisco_nxos": "cisco_nxos",
            "cisco_xr": "cisco_xr",
            "huawei_vrp": "huawei_vrp",
            "hp_comware": "hp_comware",
            "juniper_junos": "juniper_junos",
            "arista_eos": "arista_eos",
            "nokia_sros": "nokia_sros",
            "fortinet_fortios": "fortinet_fortios",
            "paloalto_panos": "paloalto_panos",
            "checkpoint_gaia": "checkpoint_gaia",
            "f5_tmsh": "f5_tmsh",
            "dell_os10": "dell_os10",
            "hp_procurve": "hp_procurve",
            "extreme_exos": "extreme_exos",
            "mikrotik_routeros": "mikrotik_routeros",
            "vyos": "vyos",
            "linux": "linux",
            "generic": "generic",
        }

        logger.info("查询结果解析器初始化完成")

    async def parse_query_results(
        self,
        nornir_results: list[NornirQueryResult],
        commands: list[str],
        devices: list[Device],
        custom_template: str | None = None,
        enable_parsing: bool = True,
    ) -> list[ParsedQueryResult]:
        """解析查询结果

        Args:
            nornir_results: Nornir查询结果列表
            commands: 执行的命令列表
            devices: 设备列表
            custom_template: 自定义模板名称
            enable_parsing: 是否启用解析

        Returns:
            解析后的查询结果列表
        """
        try:
            logger.info(f"开始解析查询结果，结果数量: {len(nornir_results)}")

            parsed_results = []
            device_map = {str(device.id): device for device in devices}

            for result in nornir_results:
                device = device_map.get(str(result.device_id)) if result.device_id else None
                if not device:
                    logger.warning(f"未找到设备信息: {result.device_id}")
                    continue

                # 获取设备平台
                platform = await self._get_device_platform(device)

                if result.success and result.commands and enable_parsing:
                    # 解析成功的结果
                    parsed_result = await self._parse_successful_result(
                        result, device, platform, commands, custom_template
                    )
                else:
                    # 处理失败的结果或不需要解析的结果
                    parsed_result = self._create_failed_result(result, device, commands)

                parsed_results.append(parsed_result)

            logger.info(f"查询结果解析完成，解析数量: {len(parsed_results)}")
            return parsed_results

        except Exception as e:
            logger.error(f"解析查询结果失败: {e}")
            raise BusinessException(f"解析查询结果失败: {e}") from e

    async def _parse_successful_result(
        self,
        result: NornirQueryResult,
        device: Device,
        platform: str,
        commands: list[str],
        custom_template: str | None = None,
    ) -> ParsedQueryResult:
        """解析成功的查询结果

        Args:
            result: Nornir查询结果
            device: 设备对象
            platform: 设备平台
            commands: 命令列表
            custom_template: 自定义模板

        Returns:
            解析后的查询结果
        """
        try:
            # 获取第一个命令的结果
            if not result.commands:
                raise ValueError("没有可用的命令结果")

            first_command = result.commands[0]
            command = first_command.command
            command_output = first_command.output

            # 使用TextFSM解析输出
            parsed_data = await self.textfsm_parser.parse_command_output(
                command_output=command_output or "",
                platform=platform,
                command=command,
                custom_template=custom_template,
            )

            # 确定使用的模板
            template_used = custom_template if custom_template else "auto-detected"
            parsing_method = "textfsm"

            # 如果解析结果为空或只有原始输出，标记为回退解析
            if not parsed_data or (len(parsed_data) == 1 and "raw_output" in parsed_data[0]):
                parsing_method = "fallback"
                template_used = "none"

            return ParsedQueryResult(
                device_id=result.device_id,
                hostname=result.hostname,
                ip_address=result.ip_address,
                command=command,
                success=True,
                raw_output=command_output,
                parsed_data=parsed_data,
                execution_time=result.total_execution_time,
                template_used=template_used,
                parsing_method=parsing_method,
            )

        except Exception as e:
            logger.error(f"解析设备 {device.hostname} 的结果失败: {e}")
            # 解析失败时返回原始结果
            raw_output = ""
            if result.commands:
                raw_output = result.commands[0].output

            return ParsedQueryResult(
                device_id=result.device_id,
                hostname=result.hostname,
                ip_address=result.ip_address,
                command=commands[0] if commands else "unknown",
                success=True,
                raw_output=raw_output,
                parsed_data=[{"error": str(e), "raw_output": raw_output}],
                execution_time=result.total_execution_time,
                template_used="none",
                parsing_method="error",
                error=f"解析失败: {e}",
            )

    def _create_failed_result(
        self, result: NornirQueryResult, device: Device, commands: list[str]
    ) -> ParsedQueryResult:
        """创建失败的查询结果

        Args:
            result: Nornir查询结果
            device: 设备对象
            commands: 命令列表

        Returns:
            失败的查询结果
        """
        raw_output = ""
        if result.commands:
            raw_output = result.commands[0].output

        return ParsedQueryResult(
            device_id=result.device_id,
            hostname=result.hostname,
            ip_address=result.ip_address,
            command=commands[0] if commands else "unknown",
            success=False,
            raw_output=raw_output,
            parsed_data=[],
            error=result.error_message,
            execution_time=result.total_execution_time,
            template_used="none",
            parsing_method="none",
        )

    async def _get_device_platform(self, device: Device) -> str:
        """获取设备平台标识

        Args:
            device: 设备对象

        Returns:
            TextFSM平台标识
        """
        try:
            # 获取设备厂商信息
            vendor = await device.vendor
            if not vendor:
                logger.warning(f"设备 {device.hostname} 没有厂商信息，使用默认平台")
                return "generic"

            # 根据厂商代码获取Scrapli平台
            from app.core.network.config import NetworkConnectionConfig

            config = NetworkConnectionConfig()
            scrapli_platform = config.scrapli_platform.VENDOR_PLATFORM_MAPPING.get(
                vendor.vendor_code.lower(), "generic"
            )

            # 映射到TextFSM平台
            textfsm_platform = self.platform_mapping.get(scrapli_platform, "generic")

            logger.debug(
                f"设备 {device.hostname} 平台映射: {vendor.vendor_code} -> {scrapli_platform} -> {textfsm_platform}"
            )
            return textfsm_platform

        except Exception as e:
            logger.error(f"获取设备平台失败: {e}")
            return "generic"

    async def parse_single_command_output(
        self, command_output: str, platform: str, command: str, custom_template: str | None = None
    ) -> dict[str, Any]:
        """解析单个命令输出

        Args:
            command_output: 命令输出
            platform: 设备平台
            command: 执行的命令
            custom_template: 自定义模板

        Returns:
            解析结果字典
        """
        try:
            parsed_data = await self.textfsm_parser.parse_command_output(
                command_output=command_output, platform=platform, command=command, custom_template=custom_template
            )

            return {
                "success": True,
                "parsed_data": parsed_data,
                "parsed_count": len(parsed_data),
                "template_used": custom_template if custom_template else "auto-detected",
                "parsing_method": "textfsm",
            }

        except Exception as e:
            logger.error(f"解析命令输出失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "parsed_data": [],
                "parsed_count": 0,
                "template_used": "none",
                "parsing_method": "error",
            }

    def get_supported_platforms(self) -> list[str]:
        """获取支持的平台列表

        Returns:
            支持的平台列表
        """
        return list(self.platform_mapping.values())

    def get_platform_mapping(self) -> dict[str, str]:
        """获取平台映射关系

        Returns:
            平台映射字典
        """
        return self.platform_mapping.copy()

    async def get_parser_stats(self) -> dict[str, Any]:
        """获取解析器统计信息

        Returns:
            统计信息字典
        """
        try:
            textfsm_stats = self.textfsm_parser.get_stats()

            return {
                "textfsm_parser": textfsm_stats,
                "supported_platforms": len(self.platform_mapping),
                "platform_mapping": self.platform_mapping,
            }

        except Exception as e:
            logger.error(f"获取解析器统计信息失败: {e}")
            return {"error": str(e)}
