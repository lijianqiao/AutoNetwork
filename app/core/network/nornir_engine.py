"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: nornir_engine.py
@DateTime: 2025/01/27
@Docs: Nornir集成 - 网络自动化任务编排和并行执行引擎
"""

import asyncio
from typing import Any
from uuid import UUID

from nornir import InitNornir
from nornir.core.inventory import Inventory
from nornir.core.task import AggregatedResult, Result, Task
from nornir_scrapli.tasks import send_command
from scrapli.exceptions import ScrapliException

from app.core.exceptions import BusinessException
from app.core.network.config import network_config
from app.core.network.interfaces import IAuthenticationProvider
from app.core.network.inventory_factory import InventoryFactory
from app.core.network.parser_integration import ParsedQueryResult, QueryResultParser
from app.models.device import Device
from app.schemas.network_query import CommandResult, NornirQueryResult
from app.utils.logger import logger


class NornirQueryEngine:
    """Nornir查询引擎 - 实现并行任务执行框架"""

    def __init__(self, auth_provider: IAuthenticationProvider | None = None):
        # 延迟导入以避免循环依赖
        from app.dao.device import DeviceDAO
        from app.dao.vendor import VendorDAO
        from app.dao.vendor_command import VendorCommandDAO

        self.device_dao = DeviceDAO()
        self.vendor_dao = VendorDAO()
        self.vendor_command_dao = VendorCommandDAO()
        self.auth_provider = auth_provider
        self.result_parser = QueryResultParser()
        self._nornir_instance = None
        self._semaphore = asyncio.Semaphore(network_config.concurrency.MAX_CONCURRENT_QUERIES)

        # 延迟导入以避免循环依赖
        if self.auth_provider is None:
            from app.services.authentication import AuthenticationManager

            self.auth_provider = AuthenticationManager()

    def _init_nornir(self, inventory: Inventory) -> None:
        """初始化Nornir实例

        Args:
            inventory: 动态构建的设备清单
        """
        try:
            # 配置Nornir
            config = {
                "inventory": {
                    "plugin": "SimpleInventory",
                    "options": {"host_file": "", "group_file": ""},
                },
                "runner": {
                    "plugin": "threaded",
                    "options": {
                        "num_workers": network_config.concurrency.MAX_CONCURRENT_QUERIES,
                    },
                },
                "logging": {
                    "enabled": False,  # 禁用Nornir日志，使用自定义日志
                },
            }

            # 初始化Nornir实例
            self._nornir_instance = InitNornir(config=config, inventory=inventory)
            logger.debug(f"Nornir实例初始化成功，设备数量: {len(inventory.hosts)}")

        except Exception as e:
            logger.error(f"Nornir实例初始化失败: {e}")
            raise BusinessException(f"Nornir初始化失败: {e}") from e

    async def _build_inventory(self, devices: list[Device], user_id: UUID | None = None) -> Inventory:
        """使用动态库存系统构建Nornir设备清单

        Args:
            devices: 设备列表
            user_id: 用户ID，用于获取认证信息

        Returns:
            Nornir设备清单
        """
        try:
            # 提取设备主机名列表
            device_hostnames = [device.hostname for device in devices]

            # 使用动态库存工厂构建清单
            inventory = await InventoryFactory.build_inventory(device_hostnames=device_hostnames, user_id=user_id)

            logger.info(
                f"使用动态库存系统构建设备清单完成，主机数量: {len(inventory.hosts)}，组数量: {len(inventory.groups)}"
            )
            return inventory

        except Exception as e:
            logger.error(f"构建设备清单失败: {e}")
            raise BusinessException(f"构建设备清单失败: {e}") from e

    def _execute_device_query(self, task: Task, commands: list[str]) -> Result:
        """执行单个设备查询任务

        Args:
            task: Nornir任务对象
            commands: 要执行的命令列表

        Returns:
            查询结果
        """
        results = []

        try:
            for command in commands:
                # 执行命令
                result = task.run(
                    task=send_command,
                    command=command,
                    name=f"执行命令: {command}",
                )
                results.append(
                    {
                        "command": command,
                        "output": result.result,
                        "failed": result.failed,
                        "exception": str(result.exception) if result.exception else None,
                    }
                )

            return Result(
                host=task.host,
                result=results,
                failed=any(r["failed"] for r in results),
            )

        except ScrapliException as e:
            logger.error(f"Scrapli连接异常: {task.host.name} - {e}")
            return Result(
                host=task.host,
                result=None,
                failed=True,
                exception=e,
            )
        except Exception as e:
            logger.error(f"设备 {task.host.name} 查询执行失败: {e}")
            return Result(
                host=task.host,
                result=None,
                failed=True,
                exception=e,
            )

    async def _process_nornir_results(self, nornir_results: AggregatedResult) -> list[NornirQueryResult]:
        """处理Nornir执行结果

        Args:
            nornir_results: Nornir聚合结果

        Returns:
            处理后的查询结果列表
        """
        results = []

        try:
            for hostname, host_result in nornir_results.items():
                # 获取设备信息
                device_data = host_result.host.data
                device_id = UUID(device_data["device_id"])
                device_hostname = hostname
                ip_address = host_result.host.hostname

                if host_result.failed:
                    # 处理失败结果
                    error_msg = str(host_result.exception) if host_result.exception else "未知错误"
                    results.append(
                        NornirQueryResult(
                            device_id=device_id,
                            hostname=device_hostname,
                            ip_address=ip_address,
                            success=False,
                            commands=[],
                            total_execution_time=0.0,
                            error_message=error_msg,
                        )
                    )
                    logger.warning(f"设备 {device_hostname} 查询失败: {error_msg}")
                else:
                    # 处理成功结果
                    command_results = []
                    total_time = 0.0

                    if hasattr(host_result, "result") and host_result.result:
                        # 如果是多任务结果，处理每个命令的结果
                        if hasattr(host_result.result, "__iter__") and not isinstance(host_result.result, str):
                            for task_result in host_result.result:
                                if isinstance(task_result, dict):
                                    command_results.append(
                                        CommandResult(
                                            command=task_result.get("command", "unknown"),
                                            output=task_result.get("output", ""),
                                            success=not task_result.get("failed", False),
                                            error_message=task_result.get("exception"),
                                            execution_time=0.0,
                                        )
                                    )
                        else:
                            # 单个结果
                            command_results.append(
                                CommandResult(
                                    command="unknown",
                                    output=str(host_result.result),
                                    success=True,
                                    execution_time=0.0,
                                )
                            )

                    results.append(
                        NornirQueryResult(
                            device_id=device_id,
                            hostname=device_hostname,
                            ip_address=ip_address,
                            success=True,
                            commands=command_results,
                            total_execution_time=total_time,
                        )
                    )
                    logger.debug(f"设备 {device_hostname} 查询成功")

            logger.info(
                f"Nornir结果处理完成，成功: {sum(1 for r in results if r.success)}，失败: {sum(1 for r in results if not r.success)}"
            )
            return results

        except Exception as e:
            logger.error(f"处理Nornir结果失败: {e}")
            raise BusinessException(f"处理查询结果失败: {e}") from e

    async def _get_vendor_command(self, template_id: UUID, vendor_id: UUID) -> list[str]:
        """获取厂商特定命令

        Args:
            template_id: 查询模板ID
            vendor_id: 厂商ID

        Returns:
            命令列表
        """
        try:
            vendor_command = await self.vendor_command_dao.get_one(template_id=template_id, vendor_id=vendor_id)
            if not vendor_command:
                raise BusinessException(f"未找到模板 {template_id} 对应厂商 {vendor_id} 的命令配置")

            return vendor_command.commands

        except Exception as e:
            logger.error(f"获取厂商命令失败: {e}")
            raise BusinessException(f"获取厂商命令失败: {e}") from e

    async def execute_parallel_query(
        self,
        devices: list[Device],
        template_id: UUID,
        query_params: dict[str, Any] | None = None,
        user_id: UUID | None = None,
    ) -> list[NornirQueryResult]:
        """执行并行查询

        Args:
            devices: 目标设备列表
            template_id: 查询模板ID
            query_params: 查询参数（用于命令模板填充）
            user_id: 用户ID，用于获取认证信息

        Returns:
            查询结果列表
        """
        async with self._semaphore:
            try:
                logger.info(f"开始并行查询，设备数量: {len(devices)}，模板ID: {template_id}")

                # 构建设备清单
                inventory = await self._build_inventory(devices, user_id)
                if not inventory.hosts:
                    raise BusinessException("没有可用的设备进行查询")

                # 初始化Nornir
                self._init_nornir(inventory)

                # 按厂商分组执行查询
                vendor_groups = {}
                for device in devices:
                    vendor = device.vendor
                    if vendor:
                        if vendor.id not in vendor_groups:
                            vendor_groups[vendor.id] = {"vendor": vendor, "devices": []}
                        vendor_groups[vendor.id]["devices"].append(device)

                # 执行查询
                all_results = []
                for vendor_id, group_data in vendor_groups.items():
                    vendor = group_data["vendor"]
                    group_devices = group_data["devices"]

                    try:
                        # 获取厂商特定命令
                        commands = await self._get_vendor_command(template_id, vendor_id)

                        # 处理命令模板参数
                        if query_params:
                            processed_commands = []
                            for cmd in commands:
                                try:
                                    processed_cmd = cmd.format(**query_params)
                                    processed_commands.append(processed_cmd)
                                except KeyError as e:
                                    logger.warning(f"命令模板参数缺失: {e}，使用原始命令: {cmd}")
                                    processed_commands.append(cmd)
                            commands = processed_commands

                        # 过滤当前厂商的设备
                        device_hostnames = [d.hostname for d in group_devices]
                        if self._nornir_instance is None:
                            raise BusinessException("Nornir实例未初始化")

                        def device_filter(host, hostnames=device_hostnames):
                            return host.name in hostnames

                        filtered_nornir = self._nornir_instance.filter(device_filter)

                        if len(filtered_nornir.inventory.hosts) == 0:
                            logger.warning(f"厂商 {vendor.vendor_name} 没有可用设备")
                            continue

                        # 执行并行查询
                        logger.info(
                            f"对厂商 {vendor.vendor_name} 的 {len(filtered_nornir.inventory.hosts)} 台设备执行查询"
                        )
                        nornir_results = filtered_nornir.run(
                            task=self._execute_device_query,
                            commands=commands,
                            name=f"查询厂商_{vendor.vendor_name}_设备",
                        )

                        # 处理结果
                        vendor_results = await self._process_nornir_results(nornir_results)
                        all_results.extend(vendor_results)

                    except Exception as e:
                        logger.error(f"厂商 {vendor.vendor_name} 查询失败: {e}")
                        # 为该厂商的所有设备创建失败结果
                        for device in group_devices:
                            all_results.append(
                                NornirQueryResult(
                                    device_id=device.id,
                                    hostname=device.hostname,
                                    ip_address=device.ip_address,
                                    success=False,
                                    commands=[],
                                    total_execution_time=0.0,
                                    error_message=f"厂商查询配置错误: {e}",
                                )
                            )

                logger.info(f"并行查询完成，总结果数: {len(all_results)}")
                return all_results

            except Exception as e:
                logger.error(f"并行查询执行失败: {e}")
                raise BusinessException(f"并行查询执行失败: {e}") from e
            finally:
                # 清理Nornir实例
                if self._nornir_instance:
                    try:
                        self._nornir_instance.close_connections()
                    except Exception as e:
                        logger.warning(f"关闭Nornir连接时出错: {e}")
                    self._nornir_instance = None

    async def get_engine_stats(self) -> dict[str, Any]:
        """获取引擎统计信息

        Returns:
            统计信息字典
        """
        return {
            "max_concurrent_queries": network_config.concurrency.MAX_CONCURRENT_QUERIES,
            "current_semaphore_value": self._semaphore._value,
            "is_nornir_active": self._nornir_instance is not None,
        }

    async def health_check(self) -> dict[str, Any]:
        """健康检查

        Returns:
            健康状态信息
        """
        try:
            stats = await self.get_engine_stats()
            return {
                "status": "healthy",
                "engine_stats": stats,
                "timestamp": asyncio.get_event_loop().time(),
            }
        except Exception as e:
            logger.error(f"Nornir引擎健康检查失败: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": asyncio.get_event_loop().time(),
            }

    async def execute_parsed_query(
        self,
        devices: list[Device],
        template_id: UUID,
        query_params: dict[str, Any] | None = None,
        user_id: UUID | None = None,
        custom_template: str | None = None,
        enable_parsing: bool = True,
    ) -> list[ParsedQueryResult]:
        """执行带解析的并行查询

        Args:
            devices: 目标设备列表
            template_id: 查询模板ID
            query_params: 查询参数（用于命令模板填充）
            user_id: 用户ID，用于获取认证信息
            custom_template: 自定义TextFSM模板名称
            enable_parsing: 是否启用解析

        Returns:
            解析后的查询结果列表
        """
        try:
            logger.info(f"开始执行带解析的并行查询，设备数量: {len(devices)}，模板ID: {template_id}")

            # 执行原始查询
            raw_results = await self.execute_parallel_query(
                devices=devices,
                template_id=template_id,
                query_params=query_params,
                user_id=user_id,
            )

            # 获取执行的命令列表（用于解析）
            commands = await self._get_executed_commands(devices, template_id)

            # 解析查询结果
            parsed_results = await self.result_parser.parse_query_results(
                nornir_results=raw_results,
                commands=commands,
                devices=devices,
                custom_template=custom_template,
                enable_parsing=enable_parsing,
            )

            logger.info(f"带解析的并行查询完成，解析结果数: {len(parsed_results)}")
            return parsed_results

        except Exception as e:
            logger.error(f"执行带解析的并行查询失败: {e}")
            raise BusinessException(f"执行带解析的并行查询失败: {e}") from e

    async def _get_executed_commands(self, devices: list[Device], template_id: UUID) -> list[str]:
        """获取执行的命令列表

        Args:
            devices: 设备列表
            template_id: 查询模板ID

        Returns:
            命令列表
        """
        try:
            # 获取第一个设备的厂商命令作为示例
            if not devices:
                return []

            device = devices[0]
            vendor = device.vendor
            if not vendor:
                return []

            commands = await self._get_vendor_command(template_id, vendor.id)
            return commands

        except Exception as e:
            logger.warning(f"获取执行命令列表失败: {e}")
            return []

    async def parse_single_output(
        self,
        command_output: str,
        platform: str,
        command: str,
        custom_template: str | None = None,
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
            return await self.result_parser.parse_single_command_output(
                command_output=command_output,
                platform=platform,
                command=command,
                custom_template=custom_template,
            )
        except Exception as e:
            logger.error(f"解析单个命令输出失败: {e}")
            raise BusinessException(f"解析单个命令输出失败: {e}") from e

    async def get_parser_stats(self) -> dict[str, Any]:
        """获取解析器统计信息

        Returns:
            解析器统计信息
        """
        try:
            return await self.result_parser.get_parser_stats()
        except Exception as e:
            logger.error(f"获取解析器统计信息失败: {e}")
            return {"error": str(e)}

    def get_supported_platforms(self) -> list[str]:
        """获取支持的解析平台列表

        Returns:
            支持的平台列表
        """
        return self.result_parser.get_supported_platforms()
