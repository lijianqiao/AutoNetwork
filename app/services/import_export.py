"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: import_export_service.py
@DateTime: 2025/07/24
@Docs: 导入导出服务层包装 - 集成日志和权限
"""

from typing import Any

from app.core.exceptions import BusinessException
from app.utils.deps import OperationContext
from app.utils.import_export import DeviceImportExportService
from app.utils.logger import logger
from app.utils.operation_logger import (
    log_create_with_context,
    log_query_with_context,
)


class ImportExportService:
    """导入导出服务层"""

    def __init__(self):
        self.device_import_export = DeviceImportExportService()

    @log_query_with_context("import_export")
    async def generate_device_template(self, file_format: str, operation_context: OperationContext) -> str:
        """生成设备导入模板"""
        try:
            if file_format not in ["xlsx", "csv"]:
                raise BusinessException("不支持的文件格式，只支持xlsx和csv")

            template_path = await self.device_import_export.export_template(file_format=file_format)
            logger.info(f"用户 {operation_context.user.username} 生成设备模板: {file_format}")
            return template_path
        except Exception as e:
            logger.error(f"生成设备模板失败: {e}")
            raise BusinessException(f"生成模板失败: {e}") from e

    @log_create_with_context("import_export")
    async def import_device_data(
        self, file_path: str, update_existing: bool, operation_context: OperationContext
    ) -> dict[str, Any]:
        """导入设备数据"""
        try:
            result = await self.device_import_export.import_data(
                file_path=file_path, operation_context=operation_context, update_existing=update_existing
            )

            logger.info(
                f"用户 {operation_context.user.username} 导入设备数据: "
                f"成功={result['success_count']}, 失败={result['error_count']}"
            )
            return result
        except Exception as e:
            logger.error(f"导入设备数据失败: {e}")
            raise BusinessException(f"导入设备数据失败: {e}") from e

    @log_query_with_context("import_export")
    async def export_device_data(
        self, devices: list[Any], file_format: str, operation_context: OperationContext
    ) -> str:
        """导出设备数据"""
        try:
            if file_format not in ["xlsx", "csv"]:
                raise BusinessException("不支持的文件格式，只支持xlsx和csv")

            export_path = await self.device_import_export.export_data(
                data=devices, file_format=file_format, operation_context=operation_context
            )

            logger.info(
                f"用户 {operation_context.user.username} 导出设备数据: 格式={file_format}, 设备数量={len(devices)}"
            )
            return export_path
        except Exception as e:
            logger.error(f"导出设备数据失败: {e}")
            raise BusinessException(f"导出设备数据失败: {e}") from e
