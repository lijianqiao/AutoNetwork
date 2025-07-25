"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: import_export.py
@DateTime: 2025/07/23
@Docs: 导入导出API端点 - 使用权限控制和服务层
"""

import asyncio
import os
import tempfile

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

from app.core.exceptions import BusinessException
from app.core.permissions.simple_decorators import Permissions, require_permission
from app.services.import_export import ImportExportService
from app.utils.deps import OperationContext, get_import_export_service
from app.utils.logger import logger


async def _safe_cleanup_temp_file(file_path: str, max_retries: int = 3, delay: float = 0.1):
    """安全清理临时文件，支持重试机制"""
    for attempt in range(max_retries):
        try:
            if os.path.exists(file_path):
                os.unlink(file_path)
                logger.debug(f"临时文件已成功删除: {file_path}")
            return
        except FileNotFoundError:
            # 文件已被删除
            return
        except PermissionError as e:
            if attempt < max_retries - 1:
                logger.warning(f"删除临时文件失败(尝试 {attempt + 1}/{max_retries}): {file_path}，等待{delay}秒后重试")
                await asyncio.sleep(delay)
                delay *= 2  # 指数退避
            else:
                logger.warning(f"无法删除临时文件(已重试{max_retries}次): {file_path}，文件可能被其他进程占用: {e}")
        except Exception as e:
            logger.error(f"删除临时文件时发生未知错误: {file_path}: {e}")
            return


class TempFileResponse(FileResponse):
    """自动清理临时文件的FileResponse"""

    def __init__(self, *args, cleanup_path: str | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.cleanup_path = cleanup_path or self.path

    async def __call__(self, scope, receive, send):
        try:
            await super().__call__(scope, receive, send)
        finally:
            # 下载完成后清理临时文件
            if self.cleanup_path:
                await _safe_cleanup_temp_file(str(self.cleanup_path))


router = APIRouter(prefix="/import-export", tags=["导入导出"])


@router.post("/devices/template", summary="生成设备导入模板")
async def generate_device_template(
    file_format: str = Form("xlsx", description="文件格式：xlsx或csv"),
    service: ImportExportService = Depends(get_import_export_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.IMPORT_EXPORT_DEVICE_TEMPLATE)),
):
    """生成设备导入模板"""
    try:
        template_path = await service.generate_device_template(
            file_format=file_format, operation_context=operation_context
        )

        # 返回文件下载，自动清理临时文件
        filename = f"设备导入模板.{file_format}"
        return TempFileResponse(
            path=template_path, filename=filename, media_type="application/octet-stream", cleanup_path=template_path
        )
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.error(f"生成设备模板失败: {e}")
        raise HTTPException(status_code=500, detail="生成模板失败") from e


@router.post("/devices/import", summary="导入设备数据")
async def import_devices(
    file: UploadFile = File(..., description="导入文件"),
    update_existing: bool = Form(False, description="是否更新已存在的设备"),
    service: ImportExportService = Depends(get_import_export_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.IMPORT_EXPORT_DEVICE_IMPORT)),
):
    """导入设备数据"""
    try:
        filename = file.filename or ""
        if not filename.endswith((".xlsx", ".csv")):
            raise HTTPException(status_code=400, detail="只支持xlsx和csv格式文件")

        # 保存上传文件到临时位置
        suffix = os.path.splitext(filename)[1]
        temp_fd, temp_path = tempfile.mkstemp(suffix=suffix)

        try:
            # 写入文件内容
            content = await file.read()
            with os.fdopen(temp_fd, "wb") as temp_file:
                temp_file.write(content)

            # 执行导入
            result = await service.import_device_data(
                file_path=temp_path, update_existing=update_existing, operation_context=operation_context
            )

            return {
                "message": "导入完成",
                "success_count": result["success_count"],
                "error_count": result["error_count"],
                "errors": result.get("errors", []),
                "imported_ids": result.get("imported_ids", []),
            }
        finally:
            # 清理临时文件 - 增强版清理机制
            await _safe_cleanup_temp_file(temp_path)

    except BusinessException as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.error(f"导入设备失败: {e}")
        raise HTTPException(status_code=500, detail="导入失败") from e


@router.post("/devices/export", summary="导出设备数据")
async def export_devices(
    file_format: str = Form("xlsx", description="文件格式：xlsx或csv"),
    service: ImportExportService = Depends(get_import_export_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.IMPORT_EXPORT_DEVICE_EXPORT)),
):
    """导出设备数据"""
    try:
        # 查询设备数据
        from app.dao.device import DeviceDAO

        device_dao = DeviceDAO()
        devices = await device_dao.get_all(include_deleted=False)  # 获取所有未删除的设备数据

        # 执行导出
        export_path = await service.export_device_data(
            devices=devices, file_format=file_format, operation_context=operation_context
        )

        # 返回文件下载，自动清理临时文件
        filename = f"设备数据导出.{file_format}"
        return TempFileResponse(
            path=export_path, filename=filename, media_type="application/octet-stream", cleanup_path=export_path
        )

    except BusinessException as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.error(f"导出设备失败: {e}")
        raise HTTPException(status_code=500, detail="导出失败") from e
