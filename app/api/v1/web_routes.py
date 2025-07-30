"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: web_routes.py
@DateTime: 2025/07/30
@Docs: Web页面路由 - 提供HTML模板页面访问
"""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.api.v1.permissions import Permissions
from app.core.permissions.simple_decorators import OperationContext, require_permission

# 创建路由器
router = APIRouter(prefix="/web", tags=["Web页面"])

# 配置模板目录
templates = Jinja2Templates(directory="templates")


@router.get("/cli-terminal", response_class=HTMLResponse, summary="获取CLI终端页面")
async def cli_terminal_page(
    request: Request, operation_context: OperationContext = Depends(require_permission(Permissions.CLI_ACCESS))
):
    """CLI终端页面

    Args:
        request: HTTP请求对象
        operation_context: 操作上下文（权限验证）

    Returns:
        CLI终端HTML页面
    """
    return templates.TemplateResponse(
        "cli_terminal.html", {"request": request, "user": operation_context.user, "title": "CLI终端管理"}
    )


@router.get("/cli-terminal-simple", response_class=HTMLResponse, summary="获取简化版CLI终端页面")
async def cli_terminal_simple_page(
    request: Request, operation_context: OperationContext = Depends(require_permission(Permissions.CLI_ACCESS))
):
    """简化版CLI终端页面（如果需要的话）

    Args:
        request: HTTP请求对象
        operation_context: 操作上下文（权限验证）

    Returns:
        简化版CLI终端HTML页面
    """
    return templates.TemplateResponse(
        "cli_terminal.html",
        {"request": request, "user": operation_context.user, "title": "CLI终端", "simple_mode": True},
    )


@router.get("/cli-terminal-test", response_class=HTMLResponse, summary="获取无需认证的CLI终端测试页面")
async def cli_terminal_test_page(
    request: Request,
    operation_context: OperationContext = Depends(require_permission(Permissions.SYSTEM_ADMIN)),
):
    """CLI终端测试页面 - 无需认证，仅供开发测试使用

    Args:
        request: HTTP请求对象

    Returns:
        CLI终端HTML页面（测试版本）
    """
    # 创建一个测试用户对象
    test_user = {"id": "test-user-id", "username": "test_user", "email": "test@example.com"}

    return templates.TemplateResponse(
        "cli_terminal.html", {"request": request, "user": test_user, "title": "CLI终端测试 - 无需认证"}
    )
