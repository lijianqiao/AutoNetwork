"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: universal_query.py
@DateTime: 2025/01/29
@Docs: 通用查询服务层 - 基于模板的查询服务，集成操作日志和权限控制
"""

from typing import Any
from uuid import UUID

from app.core.exceptions import BusinessException
from app.core.network.universal_query_engine import get_universal_query_engine
from app.schemas.universal_query import (
    TemplateCommandsPreviewRequest,
    TemplateParametersValidationRequest,
    TemplateQueryRequest,
    TemplateTypeQueryRequest,
)
from app.services.base import BaseService
from app.utils.deps import OperationContext
from app.utils.logger import logger
from app.utils.operation_logger import log_query_with_context


class UniversalQueryService(BaseService):
    """通用查询服务"""

    def __init__(self):
        self.query_engine = get_universal_query_engine()
        logger.info("通用查询服务初始化完成")

    @log_query_with_context("template_query")
    async def execute_template_query(
        self, request: TemplateQueryRequest, operation_context: OperationContext
    ) -> dict[str, Any]:
        """执行基于模板的查询

        Args:
            request: 模板查询请求
            operation_context: 操作上下文

        Returns:
            查询结果字典
        """
        try:
            logger.info(
                f"用户 {operation_context.user.username} 执行模板查询，"
                f"模板ID: {request.template_id}，设备数量: {len(request.device_ids)}"
            )

            # 调用查询引擎执行查询
            result = await self.query_engine.execute_template_query(
                template_id=request.template_id,
                device_ids=request.device_ids,
                query_params=request.query_params,
                operation_context=operation_context,
                template_version=request.template_version,
                enable_parsing=request.enable_parsing,
                custom_template=request.custom_template,
            )

            if not result.success:
                logger.error(f"模板查询执行失败: {result.error_message}")
                raise BusinessException(f"模板查询执行失败: {result.error_message}")

            logger.info(
                f"模板查询执行成功，成功设备: {result.successful_devices}/{result.total_devices}，"
                f"执行时间: {result.execution_time:.2f}秒"
            )

            return result.to_dict()

        except BusinessException:
            raise
        except Exception as e:
            logger.error(f"执行模板查询服务失败: {e}")
            raise BusinessException(f"执行模板查询服务失败: {e}") from e

    @log_query_with_context("template_type_query")
    async def execute_template_type_query(
        self, request: TemplateTypeQueryRequest, operation_context: OperationContext
    ) -> dict[str, Any]:
        """执行基于模板类型的查询

        Args:
            request: 模板类型查询请求
            operation_context: 操作上下文

        Returns:
            查询结果字典
        """
        try:
            logger.info(
                f"用户 {operation_context.user.username} 执行模板类型查询，"
                f"模板类型: {request.template_type}，设备数量: {len(request.device_ids)}"
            )

            # 调用查询引擎执行查询
            results = await self.query_engine.execute_template_query_by_type(
                template_type=request.template_type,
                device_ids=request.device_ids,
                query_params=request.query_params,
                operation_context=operation_context,
                enable_parsing=request.enable_parsing,
            )

            # 统计总体结果
            total_templates = len(results)
            successful_templates = sum(1 for r in results if r.success)
            failed_templates = total_templates - successful_templates
            total_execution_time = sum(r.execution_time for r in results)

            logger.info(
                f"模板类型查询执行完成，成功模板: {successful_templates}/{total_templates}，"
                f"总执行时间: {total_execution_time:.2f}秒"
            )

            return {
                "template_type": request.template_type,
                "query_params": request.query_params,
                "statistics": {
                    "total_templates": total_templates,
                    "successful_templates": successful_templates,
                    "failed_templates": failed_templates,
                    "total_execution_time": total_execution_time,
                },
                "results": [result.to_dict() for result in results],
                "success": successful_templates > 0,
                "error_message": None if successful_templates > 0 else "所有模板查询都失败了",
            }

        except BusinessException:
            raise
        except Exception as e:
            logger.error(f"执行模板类型查询服务失败: {e}")
            raise BusinessException(f"执行模板类型查询服务失败: {e}") from e

    @log_query_with_context("template_commands_preview")
    async def get_template_commands_preview(
        self, request: TemplateCommandsPreviewRequest, operation_context: OperationContext
    ) -> dict[str, Any]:
        """获取模板命令预览

        Args:
            request: 模板命令预览请求
            operation_context: 操作上下文

        Returns:
            命令预览信息
        """
        try:
            logger.info(f"用户 {operation_context.user.username} 获取模板命令预览，模板ID: {request.template_id}")

            # 调用查询引擎获取命令预览
            preview_data = await self.query_engine.get_template_commands_preview(
                template_id=request.template_id,
                query_params=request.query_params,
            )

            logger.info(f"模板命令预览获取成功，包含 {len(preview_data.get('vendor_commands', []))} 个厂商命令")

            return preview_data

        except BusinessException:
            raise
        except Exception as e:
            logger.error(f"获取模板命令预览失败: {e}")
            raise BusinessException(f"获取模板命令预览失败: {e}") from e

    @log_query_with_context("template_parameters_validation")
    async def validate_template_parameters(
        self, request: TemplateParametersValidationRequest, operation_context: OperationContext
    ) -> dict[str, Any]:
        """验证模板参数

        Args:
            request: 模板参数验证请求
            operation_context: 操作上下文

        Returns:
            参数验证结果
        """
        try:
            logger.info(f"用户 {operation_context.user.username} 验证模板参数，模板ID: {request.template_id}")

            # 调用查询引擎验证参数
            validation_result = await self.query_engine.validate_template_parameters(
                template_id=request.template_id,
                query_params=request.query_params,
            )

            validation_passed = validation_result.get("validation_passed", False)
            logger.info(f"模板参数验证完成，验证结果: {'通过' if validation_passed else '失败'}")

            return validation_result

        except BusinessException:
            raise
        except Exception as e:
            logger.error(f"验证模板参数失败: {e}")
            raise BusinessException(f"验证模板参数失败: {e}") from e

    @log_query_with_context("query_engine_stats")
    async def get_query_engine_stats(self, operation_context: OperationContext) -> dict[str, Any]:
        """获取查询引擎统计信息

        Args:
            operation_context: 操作上下文

        Returns:
            引擎统计信息
        """
        try:
            logger.info(f"用户 {operation_context.user.username} 获取查询引擎统计信息")

            stats = await self.query_engine.get_engine_stats()

            logger.info("查询引擎统计信息获取成功")
            return stats

        except Exception as e:
            logger.error(f"获取查询引擎统计信息失败: {e}")
            raise BusinessException(f"获取查询引擎统计信息失败: {e}") from e

    @log_query_with_context("query_engine_health")
    async def get_query_engine_health(self, operation_context: OperationContext) -> dict[str, Any]:
        """获取查询引擎健康状态

        Args:
            operation_context: 操作上下文

        Returns:
            引擎健康状态信息
        """
        try:
            logger.info(f"用户 {operation_context.user.username} 检查查询引擎健康状态")

            health = await self.query_engine.health_check()

            status = health.get("status", "unknown")
            logger.info(f"查询引擎健康检查完成，状态: {status}")

            return health

        except Exception as e:
            logger.error(f"查询引擎健康检查失败: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": None,
            }

    # ===== 便捷方法 =====

    async def execute_mac_query(
        self, device_ids: list[UUID], mac_address: str, operation_context: OperationContext
    ) -> dict[str, Any]:
        """执行MAC地址查询（便捷方法）

        Args:
            device_ids: 设备ID列表
            mac_address: MAC地址
            operation_context: 操作上下文

        Returns:
            查询结果
        """
        request = TemplateTypeQueryRequest(
            template_type="mac_query",
            device_ids=device_ids,
            query_params={"mac_address": mac_address},
            enable_parsing=True,
        )
        return await self.execute_template_type_query(request, operation_context)

    async def execute_interface_status_query(
        self,
        device_ids: list[UUID],
        operation_context: OperationContext,
        interface_pattern: str | None = None,
    ) -> dict[str, Any]:
        """执行接口状态查询（便捷方法）

        Args:
            device_ids: 设备ID列表
            interface_pattern: 接口模式（可选）
            operation_context: 操作上下文

        Returns:
            查询结果
        """
        query_params = {}
        if interface_pattern:
            query_params["interface_pattern"] = interface_pattern

        request = TemplateTypeQueryRequest(
            template_type="interface_status",
            device_ids=device_ids,
            query_params=query_params,
            enable_parsing=True,
        )
        return await self.execute_template_type_query(request, operation_context)

    async def execute_config_show_query(
        self,
        device_ids: list[UUID],
        operation_context: OperationContext,
        config_section: str | None = None,
    ) -> dict[str, Any]:
        """执行配置显示查询（便捷方法）

        Args:
            device_ids: 设备ID列表
            config_section: 配置节（可选）
            operation_context: 操作上下文

        Returns:
            查询结果
        """
        query_params = {}
        if config_section:
            query_params["config_section"] = config_section

        request = TemplateTypeQueryRequest(
            template_type="config_show",
            device_ids=device_ids,
            query_params=query_params,
            enable_parsing=True,
        )
        return await self.execute_template_type_query(request, operation_context)
