"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: network_query_clean.py
@DateTime: 2025/08/01
@Docs: 统一网络查询服务层 - 清理后的版本，消除功能重复，提供统一查询入口
"""

import time
from datetime import datetime
from typing import Any
from uuid import uuid4

from app.core.exceptions import BusinessException
from app.core.network.universal_query_engine import get_universal_query_engine
from app.dao.device import DeviceDAO
from app.dao.query_history import QueryHistoryDAO
from app.schemas.unified_query import (
    UnifiedQueryRequest,
    UnifiedQueryResponse,
    UnifiedQueryResult,
    UnifiedQuerySummary,
)
from app.services.device_connection import DeviceConnectionService
from app.services.query_history import QueryHistoryService
from app.utils.deps import OperationContext
from app.utils.logger import logger
from app.utils.operation_logger import log_query_with_context


class NetworkQueryService:
    """统一网络查询服务 - 清理版本，消除了与UniversalQueryService的功能重复"""

    def __init__(self):
        # 数据访问层
        self.device_dao = DeviceDAO()
        self.query_history_dao = QueryHistoryDAO()
        self.query_history_service = QueryHistoryService()

        # 核心服务
        self.connection_service = DeviceConnectionService()

        # 通用查询引擎 - 整合UniversalQueryService的能力
        self.universal_engine = get_universal_query_engine()

        logger.info("统一网络查询服务初始化完成（清理版本）")

    # ==================== 统一查询入口 ====================

    @log_query_with_context("unified_query")
    async def execute_unified_query(
        self, request: UnifiedQueryRequest, operation_context: OperationContext
    ) -> UnifiedQueryResponse:
        """统一查询入口 - 支持所有查询类型的唯一入口"""
        query_id = uuid4()
        start_time = time.time()

        try:
            logger.info(
                f"用户 {operation_context.user.username} 执行统一查询，"
                f"查询类型: {request.query_type}，设备数量: {len(request.device_ids)}"
            )

            # 如果提供了动态密码，设置到认证管理器的缓存中
            auth_manager = self.connection_service.auth_manager
            if request.dynamic_passwords:
                auth_manager.set_dynamic_passwords(request.dynamic_passwords)
                logger.info(f"设置了 {len(request.dynamic_passwords)} 个设备的动态密码")

            if request.region_passwords:
                auth_manager.set_region_dynamic_passwords(request.region_passwords)
                logger.info(f"设置了 {len(request.region_passwords)} 个区域的动态密码")
            try:
                # 根据查询类型分发到相应的处理方法
                result = await self._dispatch_query(request, operation_context)

                execution_time = time.time() - start_time

                # 构建统一响应
                return UnifiedQueryResponse(
                    query_id=query_id,
                    query_type=request.query_type,
                    device_results=result.get("device_results", []),
                    summary=result.get("summary", {}),
                    execution_time=execution_time,
                    created_at=datetime.now().isoformat(),
                )
            finally:
                # 查询完成后清除动态密码缓存（安全考虑）
                if request.dynamic_passwords or request.region_passwords:
                    auth_manager = self.connection_service.auth_manager
                    auth_manager.clear_dynamic_passwords()
                    logger.info("已清除动态密码缓存")

        except BusinessException:
            raise
        except Exception as e:
            logger.error(f"统一查询执行失败: {e}")
            raise BusinessException(f"统一查询执行失败: {e}") from e

    async def _dispatch_query(
        self, request: UnifiedQueryRequest, operation_context: OperationContext
    ) -> dict[str, Any]:
        """查询分发器 - 将查询请求分发到相应的处理方法"""
        match request.query_type:
            case "template":
                return await self._execute_template_query(request, operation_context)
            case "template_type":
                return await self._execute_template_type_query(request, operation_context)
            case "mac_address":
                return await self._execute_mac_query(request, operation_context)
            case "interface_status":
                return await self._execute_interface_query(request, operation_context)
            case "custom_command":
                return await self._execute_custom_command(request, operation_context)
            case _:
                raise BusinessException(f"不支持的查询类型: {request.query_type}")

    # ==================== 查询实现方法 ====================

    async def _execute_template_query(
        self, request: UnifiedQueryRequest, operation_context: OperationContext
    ) -> dict[str, Any]:
        """执行模板查询 - 委托给UniversalQueryEngine"""
        if not request.template_id:
            raise BusinessException("模板查询需要提供template_id")

        result = await self.universal_engine.execute_template_query(
            template_id=request.template_id,
            device_ids=request.device_ids,
            query_params=request.parameters or {},
            operation_context=operation_context,
            template_version=request.template_version,
            enable_parsing=request.enable_parsing,
            custom_template=request.custom_template,
        )

        return {
            "device_results": [self._convert_to_unified_result(device_result) for device_result in result.results],
            "summary": UnifiedQuerySummary(
                total_devices=result.total_devices,
                successful_devices=result.successful_devices,
                failed_devices=result.failed_devices,
                total_execution_time=result.execution_time,
                average_execution_time=result.execution_time / max(result.total_devices, 1),
            ),
        }

    async def _execute_template_type_query(
        self, request: UnifiedQueryRequest, operation_context: OperationContext
    ) -> dict[str, Any]:
        """执行模板类型查询 - 委托给UniversalQueryEngine"""
        if not request.template_type:
            raise BusinessException("模板类型查询需要提供template_type")

        results = await self.universal_engine.execute_template_query_by_type(
            template_type=request.template_type,
            device_ids=request.device_ids,
            query_params=request.parameters or {},
            operation_context=operation_context,
            enable_parsing=request.enable_parsing,
        )

        # 合并所有模板的结果
        all_device_results = []
        total_devices = 0
        successful_devices = 0
        failed_devices = 0
        total_execution_time = 0.0

        for template_result in results:
            if hasattr(template_result, "results"):
                all_device_results.extend(
                    [self._convert_to_unified_result(device_result) for device_result in template_result.results]
                )
                total_devices += template_result.total_devices
                successful_devices += template_result.successful_devices
                failed_devices += template_result.failed_devices
                total_execution_time += template_result.execution_time

        return {
            "device_results": all_device_results,
            "summary": UnifiedQuerySummary(
                total_devices=total_devices,
                successful_devices=successful_devices,
                failed_devices=failed_devices,
                total_execution_time=total_execution_time,
                average_execution_time=total_execution_time / max(total_devices, 1) if total_devices > 0 else 0,
            ),
        }

    async def _execute_mac_query(
        self, request: UnifiedQueryRequest, operation_context: OperationContext
    ) -> dict[str, Any]:
        """执行MAC查询 - 使用mac_query模板类型"""
        if not request.parameters or "mac_address" not in request.parameters:
            raise BusinessException("MAC查询需要提供mac_address参数")

        # 转换为模板类型查询
        template_request = UnifiedQueryRequest(
            query_type="template_type",
            device_ids=request.device_ids,
            template_type="mac_query",
            parameters=request.parameters,
            enable_parsing=request.enable_parsing,
            timeout=request.timeout,
            max_concurrent=request.max_concurrent,
        )
        return await self._execute_template_type_query(template_request, operation_context)

    async def _execute_interface_query(
        self, request: UnifiedQueryRequest, operation_context: OperationContext
    ) -> dict[str, Any]:
        """执行接口状态查询 - 使用interface_status模板类型"""
        # 转换为模板类型查询
        template_request = UnifiedQueryRequest(
            query_type="template_type",
            device_ids=request.device_ids,
            template_type="interface_status",
            parameters=request.parameters or {},
            enable_parsing=request.enable_parsing,
            timeout=request.timeout,
            max_concurrent=request.max_concurrent,
        )
        return await self._execute_template_type_query(template_request, operation_context)

    async def _execute_custom_command(
        self, request: UnifiedQueryRequest, operation_context: OperationContext
    ) -> dict[str, Any]:
        """执行自定义命令查询 - 直接使用连接服务"""
        if not request.parameters or "command" not in request.parameters:
            raise BusinessException("自定义命令查询需要提供command参数")

        command = request.parameters["command"]
        results = []
        successful_devices = 0
        start_time = time.time()

        for device_id in request.device_ids:
            device_start_time = time.time()
            try:
                device = await self.device_dao.get_by_id(device_id)
                if not device:
                    raise BusinessException(f"设备不存在: {device_id}")

                # 使用连接服务执行命令
                command_result = await self.connection_service.execute_command(
                    device_id=device_id,
                    command=command,
                    timeout=request.timeout,
                )

                device_execution_time = time.time() - device_start_time

                if command_result["success"]:
                    successful_devices += 1

                results.append(
                    UnifiedQueryResult(
                        device_id=device_id,
                        hostname=device.hostname,
                        ip_address=device.ip_address,
                        success=command_result["success"],
                        result_data={"command": command},
                        raw_output=command_result["output"],
                        error_message=command_result.get("error_message"),
                        execution_time=device_execution_time,
                    )
                )

            except Exception as e:
                device_execution_time = time.time() - device_start_time
                logger.error(f"设备 {device_id} 执行命令失败: {e}")
                results.append(
                    UnifiedQueryResult(
                        device_id=device_id,
                        hostname="unknown",
                        ip_address="unknown",
                        success=False,
                        result_data=None,
                        raw_output=None,
                        error_message=str(e),
                        execution_time=device_execution_time,
                    )
                )

        total_execution_time = time.time() - start_time

        return {
            "device_results": results,
            "summary": UnifiedQuerySummary(
                total_devices=len(request.device_ids),
                successful_devices=successful_devices,
                failed_devices=len(request.device_ids) - successful_devices,
                total_execution_time=total_execution_time,
                average_execution_time=total_execution_time / max(len(request.device_ids), 1),
            ),
        }

    def _convert_to_unified_result(self, parsed_result) -> UnifiedQueryResult:
        """将ParsedQueryResult转换为统一结果格式"""
        return UnifiedQueryResult(
            device_id=parsed_result.device_id,
            hostname=parsed_result.hostname,
            ip_address=parsed_result.ip_address,
            success=parsed_result.success,
            result_data={"parsed_data": parsed_result.parsed_data, "command": parsed_result.command},
            raw_output=parsed_result.raw_output,
            error_message=parsed_result.error,
            execution_time=parsed_result.execution_time,
        )
