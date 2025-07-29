"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: universal_query_engine.py
@DateTime: 2025/01/29
@Docs: 通用查询引擎 - 基于查询模板的统一查询接口，扩展现有NornirQueryEngine
"""

import asyncio
from datetime import datetime
from typing import Any
from uuid import UUID

from app.core.exceptions import BusinessException
from app.core.network.nornir_engine import NornirQueryEngine
from app.core.network.parser_integration import ParsedQueryResult
from app.dao.device import DeviceDAO
from app.dao.query_template import QueryTemplateDAO
from app.dao.vendor_command import VendorCommandDAO
from app.models.device import Device
from app.models.query_template import QueryTemplate
from app.services.query_history import QueryHistoryService
from app.utils.deps import OperationContext
from app.utils.logger import logger


class TemplateQueryResult:
    """基于模板的查询结果"""

    def __init__(
        self,
        template_id: UUID,
        template_name: str,
        template_type: str,
        template_version: int,
        query_params: dict[str, Any] | None = None,
        results: list[ParsedQueryResult] | None = None,
        success: bool = True,
        error_message: str | None = None,
        execution_time: float = 0.0,
        query_history_id: UUID | None = None,
        total_devices: int = 0,
        successful_devices: int = 0,
        failed_devices: int = 0,
    ):
        self.template_id = template_id
        self.template_name = template_name
        self.template_type = template_type
        self.template_version = template_version
        self.query_params = query_params or {}
        self.results = results or []
        self.success = success
        self.error_message = error_message
        self.execution_time = execution_time
        self.query_history_id = query_history_id
        self.total_devices = total_devices
        self.successful_devices = successful_devices
        self.failed_devices = failed_devices
        self.executed_at = datetime.now()

    def to_dict(self) -> dict[str, Any]:
        """转换为字典格式"""
        return {
            "template_id": str(self.template_id),
            "template_name": self.template_name,
            "template_type": self.template_type,
            "template_version": self.template_version,
            "query_params": self.query_params,
            "results": [result.to_dict() for result in self.results],
            "success": self.success,
            "error_message": self.error_message,
            "execution_time": self.execution_time,
            "query_history_id": str(self.query_history_id) if self.query_history_id else None,
            "statistics": {
                "total_devices": self.total_devices,
                "successful_devices": self.successful_devices,
                "failed_devices": self.failed_devices,
                "success_rate": (self.successful_devices / max(self.total_devices, 1)) * 100,
                "total_results": len(self.results),
            },
            "executed_at": self.executed_at.isoformat(),
        }


class UniversalQueryEngine:
    """通用查询引擎 - 基于查询模板的统一查询接口，扩展NornirQueryEngine"""

    def __init__(self):
        # 复用现有的NornirQueryEngine
        self.nornir_engine = NornirQueryEngine()

        # DAO实例
        self.template_dao = QueryTemplateDAO()
        self.vendor_command_dao = VendorCommandDAO()
        self.device_dao = DeviceDAO()

        # 服务实例
        self.query_history_service = QueryHistoryService()

        # 并发控制
        self._semaphore = asyncio.Semaphore(10)  # 限制并发查询数

        logger.info("通用查询引擎初始化完成")

    async def execute_template_query(
        self,
        template_id: UUID,
        device_ids: list[UUID],
        query_params: dict[str, Any] | None = None,
        operation_context: OperationContext | None = None,
        template_version: int | None = None,
        enable_parsing: bool = True,
        custom_template: str | None = None,
    ) -> TemplateQueryResult:
        """基于模板执行查询

        Args:
            template_id: 查询模板ID
            device_ids: 目标设备ID列表
            query_params: 查询参数（用于命令模板填充）
            operation_context: 操作上下文（包含用户信息）
            template_version: 指定模板版本（None为最新版本）
            enable_parsing: 是否启用结果解析
            custom_template: 自定义TextFSM模板名称

        Returns:
            模板查询结果
        """
        async with self._semaphore:
            start_time = datetime.now()
            query_history_id = None

            try:
                logger.info(f"开始基于模板 {template_id} 执行查询，设备数量: {len(device_ids)}")

                # 1. 获取并验证查询模板
                template = await self._get_and_validate_template(template_id, template_version)

                # 2. 获取并验证设备列表
                devices = await self._get_and_validate_devices(device_ids)

                # 3. 验证模板是否有对应的厂商命令
                await self._validate_template_commands(template, devices)

                # 4. 执行查询
                parsed_results = await self._execute_query_with_template(
                    template, devices, query_params, operation_context, enable_parsing, custom_template
                )

                # 5. 计算统计信息
                total_devices = len(devices)
                successful_devices = sum(1 for result in parsed_results if result.success)
                failed_devices = total_devices - successful_devices
                execution_time = (datetime.now() - start_time).total_seconds()

                # 6. 记录查询历史（一次性完整记录）
                if operation_context:
                    query_history_id = await self._create_query_history(
                        template, devices, query_params, operation_context, parsed_results, execution_time
                    )

                # 8. 构建查询结果
                result = TemplateQueryResult(
                    template_id=template.id,
                    template_name=template.template_name,
                    template_type=template.template_type,
                    template_version=template.version,
                    query_params=query_params,
                    results=parsed_results,
                    success=True,
                    execution_time=execution_time,
                    query_history_id=query_history_id,
                    total_devices=total_devices,
                    successful_devices=successful_devices,
                    failed_devices=failed_devices,
                )

                logger.info(
                    f"模板查询完成，成功设备: {successful_devices}/{total_devices}，执行时间: {execution_time:.2f}秒"
                )

                return result

            except Exception as e:
                execution_time = (datetime.now() - start_time).total_seconds()
                logger.error(f"基于模板 {template_id} 的查询失败: {e}")

                # 记录失败的查询历史
                if operation_context:
                    try:
                        from app.schemas.query_history import QueryHistoryCreateRequest

                        # 尝试获取模板信息用于记录
                        template_info = None
                        devices_info = []
                        try:
                            template_info = await self._get_and_validate_template(template_id, template_version)
                            devices_info = await self._get_and_validate_devices(device_ids)
                        except Exception:
                            pass

                        history_request = QueryHistoryCreateRequest(
                            query_type=template_info.template_type if template_info else "unknown",
                            query_params=query_params or {},
                            target_devices=[device.hostname for device in devices_info] if devices_info else [],
                            status="failed",
                            execution_time=execution_time,
                            error_message=f"查询失败: {str(e)}",
                        )

                        history = await self.query_history_service.create_history(history_request, operation_context)
                        query_history_id = history.id

                    except Exception as history_error:
                        logger.error(f"记录失败查询历史时出错: {history_error}")
                        query_history_id = None

                # 返回失败结果
                return TemplateQueryResult(
                    template_id=template_id,
                    template_name="Unknown",
                    template_type="Unknown",
                    template_version=0,
                    query_params=query_params,
                    results=[],
                    success=False,
                    error_message=str(e),
                    execution_time=execution_time,
                    query_history_id=query_history_id,
                    total_devices=len(device_ids),
                    successful_devices=0,
                    failed_devices=len(device_ids),
                )

    async def execute_template_query_by_type(
        self,
        template_type: str,
        device_ids: list[UUID],
        query_params: dict[str, Any] | None = None,
        operation_context: OperationContext | None = None,
        enable_parsing: bool = True,
    ) -> list[TemplateQueryResult]:
        """根据模板类型执行查询（获取该类型下所有激活的模板）

        Args:
            template_type: 模板类型 (mac_query, interface_status, config_show)
            device_ids: 目标设备ID列表
            query_params: 查询参数
            operation_context: 操作上下文
            enable_parsing: 是否启用结果解析

        Returns:
            查询结果列表
        """
        try:
            logger.info(f"开始执行模板类型 {template_type} 的查询")

            # 获取该类型下所有激活的模板
            templates = await self.template_dao.get_by_template_type(template_type)
            active_templates = [t for t in templates if t.is_active]

            if not active_templates:
                raise BusinessException(f"模板类型 {template_type} 下没有激活的模板")

            # 并发执行所有模板查询
            tasks = [
                self.execute_template_query(
                    template_id=template.id,
                    device_ids=device_ids,
                    query_params=query_params,
                    operation_context=operation_context,
                    enable_parsing=enable_parsing,
                )
                for template in active_templates
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # 处理结果，将异常转换为失败的查询结果
            query_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    template = active_templates[i]
                    query_results.append(
                        TemplateQueryResult(
                            template_id=template.id,
                            template_name=template.template_name,
                            template_type=template.template_type,
                            template_version=template.version,
                            query_params=query_params,
                            results=[],
                            success=False,
                            error_message=str(result),
                            total_devices=len(device_ids),
                            successful_devices=0,
                            failed_devices=len(device_ids),
                        )
                    )
                else:
                    query_results.append(result)

            logger.info(f"模板类型 {template_type} 的查询完成，执行了 {len(query_results)} 个模板")
            return query_results

        except Exception as e:
            logger.error(f"模板类型 {template_type} 的查询失败: {e}")
            raise BusinessException(f"模板类型查询失败: {e}") from e

    async def get_template_commands_preview(
        self, template_id: UUID, query_params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """预览模板命令（不执行，仅显示命令内容）

        Args:
            template_id: 模板ID
            query_params: 查询参数（用于命令模板填充）

        Returns:
            模板命令预览信息
        """
        try:
            # 获取模板信息
            template = await self._get_and_validate_template(template_id)

            # 获取所有厂商命令
            vendor_commands = await self.vendor_command_dao.get_by_template(template_id)

            if not vendor_commands:
                raise BusinessException(f"模板 {template.template_name} 没有配置厂商命令")

            # 构建预览信息
            preview_data = {
                "template_info": {
                    "template_id": str(template.id),
                    "template_name": template.template_name,
                    "template_type": template.template_type,
                    "description": template.description,
                    "version": template.version,
                    "is_active": template.is_active,
                },
                "vendor_commands": [],
                "query_params": query_params or {},
            }

            # 处理每个厂商的命令
            for vendor_command in vendor_commands:
                # 获取关联的厂商信息
                vendor = await vendor_command.vendor
                if not vendor:
                    continue

                # 处理命令模板参数
                processed_commands = []
                raw_commands = vendor_command.commands if isinstance(vendor_command.commands, list) else []

                for cmd in raw_commands:
                    try:
                        if query_params:
                            processed_cmd = cmd.format(**query_params)
                        else:
                            processed_cmd = cmd
                        processed_commands.append(
                            {
                                "raw_command": cmd,
                                "processed_command": processed_cmd,
                                "has_parameters": "{" in cmd and "}" in cmd,
                            }
                        )
                    except KeyError as e:
                        processed_commands.append(
                            {
                                "raw_command": cmd,
                                "processed_command": cmd,
                                "has_parameters": True,
                                "missing_parameter": str(e),
                            }
                        )

                vendor_info = {
                    "vendor_id": str(vendor.id),
                    "vendor_code": vendor.vendor_code,
                    "vendor_name": vendor.vendor_name,
                    "scrapli_platform": vendor.scrapli_platform,
                    "commands": processed_commands,
                    "parser_type": vendor_command.parser_type,
                    "has_parser_template": bool(vendor_command.parser_template),
                }

                preview_data["vendor_commands"].append(vendor_info)

            return preview_data

        except Exception as e:
            logger.error(f"获取模板命令预览失败: {e}")
            raise BusinessException(f"获取模板命令预览失败: {e}") from e

    async def validate_template_parameters(self, template_id: UUID, query_params: dict[str, Any]) -> dict[str, Any]:
        """验证模板参数完整性

        Args:
            template_id: 模板ID
            query_params: 查询参数

        Returns:
            参数验证结果
        """
        try:
            # 获取模板信息
            template = await self._get_and_validate_template(template_id)

            # 获取所有厂商命令
            vendor_commands = await self.vendor_command_dao.get_by_template(template_id)

            if not vendor_commands:
                raise BusinessException(f"模板 {template.template_name} 没有配置厂商命令")

            validation_result = {
                "template_id": str(template_id),
                "template_name": template.template_name,
                "provided_params": query_params,
                "validation_passed": True,
                "vendor_validations": [],
                "required_params": set(),
                "missing_params": set(),
                "unused_params": set(),
            }

            all_required_params = set()

            # 验证每个厂商的命令参数
            for vendor_command in vendor_commands:
                vendor = await vendor_command.vendor
                if not vendor:
                    continue

                vendor_validation = {
                    "vendor_code": vendor.vendor_code,
                    "vendor_name": vendor.vendor_name,
                    "required_params": set(),
                    "missing_params": set(),
                    "validation_passed": True,
                }

                # 分析命令中的参数
                commands = vendor_command.commands if isinstance(vendor_command.commands, list) else []
                for cmd in commands:
                    # 使用正则表达式提取参数名
                    import re

                    param_pattern = r"\{(\w+)\}"
                    found_params = set(re.findall(param_pattern, cmd))
                    vendor_validation["required_params"].update(found_params)
                    all_required_params.update(found_params)

                # 检查缺失的参数
                provided_params = set(query_params.keys())
                missing_params = vendor_validation["required_params"] - provided_params
                vendor_validation["missing_params"] = missing_params

                if missing_params:
                    vendor_validation["validation_passed"] = False
                    validation_result["validation_passed"] = False

                # 转换为列表以便JSON序列化
                vendor_validation["required_params"] = list(vendor_validation["required_params"])
                vendor_validation["missing_params"] = list(vendor_validation["missing_params"])

                validation_result["vendor_validations"].append(vendor_validation)

            # 计算全局参数信息
            provided_params = set(query_params.keys())
            validation_result["required_params"] = list(all_required_params)
            validation_result["missing_params"] = list(all_required_params - provided_params)
            validation_result["unused_params"] = list(provided_params - all_required_params)

            return validation_result

        except Exception as e:
            logger.error(f"验证模板参数失败: {e}")
            raise BusinessException(f"验证模板参数失败: {e}") from e

    # ===== 私有方法 =====

    async def _get_and_validate_template(self, template_id: UUID, template_version: int | None = None) -> QueryTemplate:
        """获取并验证查询模板"""
        template = await self.template_dao.get_by_id(template_id)
        if not template:
            raise BusinessException(f"查询模板不存在: {template_id}")

        if not template.is_active:
            raise BusinessException(f"查询模板 '{template.template_name}' 未激活")

        # TODO: 如果需要版本控制，可以在这里添加版本验证逻辑
        # if template_version is not None and template.version != template_version:
        #     raise BusinessException(f"模板版本不匹配，当前版本: {template.version}，请求版本: {template_version}")

        return template

    async def _get_and_validate_devices(self, device_ids: list[UUID]) -> list[Device]:
        """获取并验证设备列表"""
        if not device_ids:
            raise BusinessException("设备列表不能为空")

        devices = await self.device_dao.get_by_ids(device_ids)
        if len(devices) != len(device_ids):
            found_ids = {device.id for device in devices}
            missing_ids = set(device_ids) - found_ids
            raise BusinessException(f"以下设备不存在: {missing_ids}")

        # 过滤非活跃设备
        active_devices = [device for device in devices if device.is_active]
        if len(active_devices) != len(devices):
            inactive_count = len(devices) - len(active_devices)
            logger.warning(f"跳过了 {inactive_count} 个非活跃设备")

        if not active_devices:
            raise BusinessException("没有活跃的设备可供查询")

        return active_devices

    async def _validate_template_commands(self, template: QueryTemplate, devices: list[Device]) -> None:
        """验证模板是否有对应设备厂商的命令配置"""
        # 获取设备的厂商列表
        vendor_ids = set()
        for device in devices:
            vendor = await device.vendor
            if vendor:
                vendor_ids.add(vendor.id)

        if not vendor_ids:
            raise BusinessException("设备缺少厂商信息")

        # 检查模板是否为这些厂商配置了命令
        for vendor_id in vendor_ids:
            vendor_command = await self.vendor_command_dao.get_by_template_and_vendor(template.id, vendor_id)
            if not vendor_command:
                # 获取厂商信息用于错误提示
                from app.dao.vendor import VendorDAO

                vendor_dao = VendorDAO()
                vendor = await vendor_dao.get_by_id(vendor_id)
                vendor_name = vendor.vendor_name if vendor else str(vendor_id)
                raise BusinessException(f"查询模板 '{template.template_name}' 没有为厂商 '{vendor_name}' 配置命令")

    async def _execute_query_with_template(
        self,
        template: QueryTemplate,
        devices: list[Device],
        query_params: dict[str, Any] | None,
        operation_context: OperationContext | None,
        enable_parsing: bool,
        custom_template: str | None,
    ) -> list[ParsedQueryResult]:
        """使用模板执行查询"""
        try:
            # 调用现有的NornirQueryEngine执行查询
            user_id = operation_context.user.id if operation_context and operation_context.user else None

            if enable_parsing:
                # 执行带解析的查询
                parsed_results = await self.nornir_engine.execute_parsed_query(
                    devices=devices,
                    template_id=template.id,
                    query_params=query_params,
                    user_id=user_id,
                    custom_template=custom_template,
                    enable_parsing=enable_parsing,
                )
            else:
                # 执行原始查询
                raw_results = await self.nornir_engine.execute_parallel_query(
                    devices=devices,
                    template_id=template.id,
                    query_params=query_params,
                    user_id=user_id,
                )

                # 转换为ParsedQueryResult格式
                parsed_results = []
                for raw_result in raw_results:
                    if raw_result.success and raw_result.commands:
                        first_command = raw_result.commands[0]
                        parsed_result = ParsedQueryResult(
                            device_id=raw_result.device_id,
                            hostname=raw_result.hostname,
                            ip_address=raw_result.ip_address,
                            command=first_command.command,
                            success=True,
                            raw_output=first_command.output,
                            parsed_data=[{"raw_output": first_command.output}],
                            execution_time=raw_result.total_execution_time,
                            template_used="none",
                            parsing_method="raw",
                        )
                    else:
                        parsed_result = ParsedQueryResult(
                            device_id=raw_result.device_id,
                            hostname=raw_result.hostname,
                            ip_address=raw_result.ip_address,
                            command="unknown",
                            success=False,
                            raw_output="",
                            parsed_data=[],
                            error=raw_result.error_message,
                            execution_time=raw_result.total_execution_time,
                            template_used="none",
                            parsing_method="none",
                        )
                    parsed_results.append(parsed_result)

            return parsed_results

        except Exception as e:
            logger.error(f"执行模板查询失败: {e}")
            raise BusinessException(f"执行模板查询失败: {e}") from e

    async def _create_query_history(
        self,
        template: QueryTemplate,
        devices: list[Device],
        query_params: dict[str, Any] | None,
        operation_context: OperationContext,
        results: list[ParsedQueryResult],
        execution_time: float,
    ) -> UUID | None:
        """创建查询历史记录（一次性完整记录）"""
        try:
            from app.schemas.query_history import QueryHistoryCreateRequest

            # 计算查询状态
            successful_count = sum(1 for result in results if result.success)
            total_count = len(results)

            if successful_count == 0:
                status = "failed"
            elif successful_count == total_count:
                status = "success"
            else:
                status = "partial"

            history_request = QueryHistoryCreateRequest(
                query_type=template.template_type,
                query_params=query_params or {},
                target_devices=[device.hostname for device in devices],
                status=status,
                execution_time=execution_time,
                error_message=f"成功: {successful_count}/{total_count} 设备",
            )

            history = await self.query_history_service.create_history(history_request, operation_context)
            return history.id

        except Exception as e:
            logger.error(f"创建查询历史失败: {e}")
            # 不因为历史记录失败而中断查询
            return None

    async def get_engine_stats(self) -> dict[str, Any]:
        """获取引擎统计信息"""
        try:
            # 获取底层Nornir引擎统计
            nornir_stats = await self.nornir_engine.get_engine_stats()

            # 获取模板统计
            total_templates = await self.template_dao.count()
            active_templates = await self.template_dao.count(is_active=True)
            total_vendor_commands = await self.vendor_command_dao.count()

            return {
                "universal_query_engine": {
                    "semaphore_value": self._semaphore._value,
                    "max_concurrent_queries": 10,
                },
                "template_stats": {
                    "total_templates": total_templates,
                    "active_templates": active_templates,
                    "inactive_templates": total_templates - active_templates,
                    "total_vendor_commands": total_vendor_commands,
                },
                "nornir_engine": nornir_stats,
            }

        except Exception as e:
            logger.error(f"获取引擎统计信息失败: {e}")
            return {"error": str(e)}

    async def health_check(self) -> dict[str, Any]:
        """健康检查"""
        try:
            # 检查底层引擎
            nornir_health = await self.nornir_engine.health_check()

            # 检查数据库连接
            template_check = await self.template_dao.count() >= 0
            vendor_command_check = await self.vendor_command_dao.count() >= 0

            overall_healthy = nornir_health.get("status") == "healthy" and template_check and vendor_command_check

            return {
                "status": "healthy" if overall_healthy else "unhealthy",
                "components": {
                    "nornir_engine": nornir_health,
                    "template_dao": "healthy" if template_check else "unhealthy",
                    "vendor_command_dao": "healthy" if vendor_command_check else "unhealthy",
                },
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"通用查询引擎健康检查失败: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }


# 全局实例
_universal_query_engine: UniversalQueryEngine | None = None


def get_universal_query_engine() -> UniversalQueryEngine:
    """获取全局通用查询引擎实例"""
    global _universal_query_engine
    if _universal_query_engine is None:
        _universal_query_engine = UniversalQueryEngine()
    return _universal_query_engine
