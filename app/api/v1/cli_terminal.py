"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: cli_terminal.py
@DateTime: 2025/07/30
@Docs: CLI终端API - WebSocket CLI终端的REST API接口
"""

import json
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, status

from app.api.v1.permissions import Permissions
from app.core.exceptions import BusinessException
from app.core.permissions.simple_decorators import OperationContext, require_permission
from app.schemas.base import BaseResponse, SuccessResponse
from app.schemas.cli import DeviceConnectionConfig, PlatformInfo, SessionInfo, SessionStats, ValidationResult
from app.services.cli_session import CLISessionService
from app.utils.deps import get_cli_service
from app.utils.logger import logger

router = APIRouter(prefix="/cli", tags=["CLI终端"])


@router.websocket("/terminal/device/{device_id}", name="连接设备CLI终端")
async def connect_device_terminal(
    websocket: WebSocket,
    device_id: UUID,
    dynamic_password: str | None = None,
    operation_context: OperationContext = Depends(require_permission(Permissions.CLI_ACCESS)),
    cli_service: CLISessionService = Depends(get_cli_service),
):
    """连接到数据库中设备的CLI终端

    Args:
        websocket: WebSocket连接
        device_id: 设备ID
        dynamic_password: 动态密码（可选）
        operation_context: 操作上下文
        cli_service: CLI会话服务
    """
    await websocket.accept()
    session = None

    try:
        # 创建CLI会话
        session = await cli_service.create_device_session(
            device_id=device_id,
            websocket=websocket,
            operation_context=operation_context,
            dynamic_password=dynamic_password,
        )

        # 发送连接成功消息
        await websocket.send_text(
            json.dumps(
                {
                    "type": "connection_status",
                    "status": "connected",
                    "session_id": session.session_id,
                    "message": f"已连接到设备: {session.device.hostname if session.device else 'Unknown'}",
                }
            )
        )

        # 发送初始提示符
        initial_prompt = session._device_prompt or "# "
        await websocket.send_text(json.dumps({"type": "output", "data": f"\r\n欢迎使用CLI终端\r\n{initial_prompt}"}))

        # 处理WebSocket消息
        while True:
            try:
                # 接收用户输入
                message = await websocket.receive_text()
                message_data = json.loads(message)

                if message_data.get("type") == "input":
                    user_input = message_data.get("data", "")

                    # 发送输入到设备
                    response = await cli_service.send_session_input(
                        session_id=session.session_id, user_input=user_input, operation_context=operation_context
                    )

                    # 发送设备响应
                    if response:
                        await websocket.send_text(json.dumps({"type": "output", "data": response}))

                elif message_data.get("type") == "ping":
                    # 心跳检测
                    await websocket.send_text(json.dumps({"type": "pong"}))

                elif message_data.get("type") == "reconnect":
                    # 重连请求
                    success = await cli_service.reconnect_session(
                        session_id=session.session_id,
                        operation_context=operation_context,
                        dynamic_password=message_data.get("dynamic_password"),
                    )

                    await websocket.send_text(
                        json.dumps(
                            {
                                "type": "connection_status",
                                "status": "connected" if success else "disconnected",
                                "message": "重连成功" if success else "重连失败",
                            }
                        )
                    )

            except WebSocketDisconnect:
                logger.info(f"WebSocket连接断开: 会话 {session.session_id if session else 'unknown'}")
                break

            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({"type": "error", "message": "无效的JSON格式"}))

            except Exception as e:
                logger.error(f"处理WebSocket消息失败: {e}")
                await websocket.send_text(json.dumps({"type": "error", "message": f"处理消息失败: {e}"}))

    except BusinessException as e:
        await websocket.send_text(json.dumps({"type": "error", "message": str(e)}))

    except Exception as e:
        logger.error(f"CLI WebSocket连接失败: {e}")
        await websocket.send_text(json.dumps({"type": "error", "message": f"连接失败: {e}"}))

    finally:
        # 清理会话
        if session:
            try:
                await cli_service.close_session(session_id=session.session_id, operation_context=operation_context)
            except Exception as e:
                logger.error(f"清理CLI会话失败: {e}")


@router.websocket("/terminal/manual", name="连接手动配置设备CLI终端")
async def connect_manual_terminal(
    websocket: WebSocket,
    operation_context: OperationContext = Depends(require_permission(Permissions.CLI_ACCESS)),
    cli_service: CLISessionService = Depends(get_cli_service),
):
    """连接到手动配置设备的CLI终端

    Args:
        websocket: WebSocket连接
        operation_context: 操作上下文
        cli_service: CLI会话服务
    """
    await websocket.accept()
    session = None

    try:
        # 等待设备配置信息
        config_message = await websocket.receive_text()
        config_data = json.loads(config_message)

        if config_data.get("type") != "device_config":
            await websocket.send_text(json.dumps({"type": "error", "message": "请先发送设备配置信息"}))
            return

        device_config = config_data.get("config", {})

        # 验证设备配置
        validation_result = await cli_service.validate_device_connection(
            device_config=device_config, operation_context=operation_context
        )

        if not validation_result["valid"]:
            await websocket.send_text(json.dumps({"type": "error", "message": validation_result["error"]}))
            return

        # 创建CLI会话
        session = await cli_service.create_manual_session(
            device_config=device_config, websocket=websocket, operation_context=operation_context
        )

        # 发送连接成功消息
        await websocket.send_text(
            json.dumps(
                {
                    "type": "connection_status",
                    "status": "connected",
                    "session_id": session.session_id,
                    "message": f"已连接到设备: {device_config['ip_address']}",
                }
            )
        )

        # 发送初始提示符
        initial_prompt = session._device_prompt or "# "
        await websocket.send_text(json.dumps({"type": "output", "data": f"\r\n欢迎使用CLI终端\r\n{initial_prompt}"}))

        # 处理WebSocket消息 (与设备终端相同的逻辑)
        while True:
            try:
                message = await websocket.receive_text()
                message_data = json.loads(message)

                if message_data.get("type") == "input":
                    user_input = message_data.get("data", "")

                    response = await cli_service.send_session_input(
                        session_id=session.session_id, user_input=user_input, operation_context=operation_context
                    )

                    if response:
                        await websocket.send_text(json.dumps({"type": "output", "data": response}))

                elif message_data.get("type") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))

            except WebSocketDisconnect:
                logger.info(f"WebSocket连接断开: 会话 {session.session_id if session else 'unknown'}")
                break

            except Exception as e:
                logger.error(f"处理WebSocket消息失败: {e}")
                await websocket.send_text(json.dumps({"type": "error", "message": f"处理消息失败: {e}"}))

    except Exception as e:
        logger.error(f"CLI WebSocket连接失败: {e}")
        await websocket.send_text(json.dumps({"type": "error", "message": f"连接失败: {e}"}))

    finally:
        if session:
            try:
                await cli_service.close_session(session_id=session.session_id, operation_context=operation_context)
            except Exception as e:
                logger.error(f"清理CLI会话失败: {e}")


# REST API端点
@router.get("/sessions", response_model=BaseResponse[list[SessionInfo]], summary="获取当前用户的所有CLI会话")
async def get_user_sessions(
    operation_context: OperationContext = Depends(require_permission(Permissions.CLI_ACCESS)),
    cli_service: CLISessionService = Depends(get_cli_service),
):
    """获取当前用户的所有CLI会话"""
    try:
        sessions = await cli_service.get_user_sessions(operation_context)
        return BaseResponse(data=sessions, message="获取CLI会话成功")
    except Exception as e:
        logger.error(f"获取用户CLI会话失败: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取会话失败: {e}") from e


@router.get("/sessions/all", response_model=BaseResponse[list[SessionInfo]], summary="获取所有CLI会话（管理员功能）")
async def get_all_sessions(
    operation_context: OperationContext = Depends(require_permission(Permissions.CLI_EXECUTE)),  # 需要更高权限
    cli_service: CLISessionService = Depends(get_cli_service),
):
    """获取所有CLI会话（管理员功能）"""
    try:
        sessions = await cli_service.get_all_sessions(operation_context)
        return BaseResponse(data=sessions, message="获取所有CLI会话成功")
    except Exception as e:
        logger.error(f"获取所有CLI会话失败: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取会话失败: {e}") from e


@router.get("/sessions/stats", response_model=BaseResponse[SessionStats], summary="获取CLI会话统计信息")
async def get_session_stats(
    operation_context: OperationContext = Depends(require_permission(Permissions.CLI_ACCESS)),
    cli_service: CLISessionService = Depends(get_cli_service),
):
    """获取CLI会话统计信息"""
    try:
        stats = await cli_service.get_session_stats()
        return BaseResponse(data=stats, message="获取CLI会话统计成功")
    except Exception as e:
        logger.error(f"获取CLI会话统计失败: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取统计失败: {e}") from e


@router.delete("/sessions/{session_id}", response_model=SuccessResponse, summary="关闭指定的CLI会话")
async def close_session(
    session_id: str,
    operation_context: OperationContext = Depends(require_permission(Permissions.CLI_ACCESS)),
    cli_service: CLISessionService = Depends(get_cli_service),
):
    """关闭指定的CLI会话"""
    try:
        success = await cli_service.close_session(session_id, operation_context)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会话不存在")
        return SuccessResponse(message=f"会话 {session_id} 已关闭")
    except BusinessException as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e
    except Exception as e:
        logger.error(f"关闭CLI会话失败: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"关闭会话失败: {e}") from e


@router.get("/platforms", response_model=BaseResponse[list[PlatformInfo]], summary="获取支持的设备平台列表")
async def get_supported_platforms(
    operation_context: OperationContext = Depends(require_permission(Permissions.CLI_ACCESS)),
    cli_service: CLISessionService = Depends(get_cli_service),
):
    """获取支持的设备平台列表"""
    try:
        platforms = await cli_service.get_supported_platforms()
        return BaseResponse(data=platforms, message="获取支持平台列表成功")
    except Exception as e:
        logger.error(f"获取支持平台失败: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取平台失败: {e}") from e


@router.post("/validate-config", response_model=BaseResponse[ValidationResult], summary="验证设备连接配置")
async def validate_device_config(
    config: DeviceConnectionConfig,
    operation_context: OperationContext = Depends(require_permission(Permissions.CLI_ACCESS)),
    cli_service: CLISessionService = Depends(get_cli_service),
):
    """验证设备连接配置"""
    try:
        result = await cli_service.validate_device_connection(
            device_config=config.dict(), operation_context=operation_context
        )
        return BaseResponse(data=result, message="设备配置验证完成")
    except Exception as e:
        logger.error(f"验证设备配置失败: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"验证失败: {e}") from e


@router.get("/sessions/{session_id}", response_model=BaseResponse[SessionInfo], summary="获取指定会话的详细信息")
async def get_session_info(
    session_id: str,
    operation_context: OperationContext = Depends(require_permission(Permissions.CLI_ACCESS)),
    cli_service: CLISessionService = Depends(get_cli_service),
):
    """获取指定会话的详细信息"""
    try:
        session = await cli_service.get_session(session_id)
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会话不存在")

        # 检查权限 - 只能查看自己的会话
        if session.user_id != operation_context.user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="没有权限访问此会话")

        return BaseResponse(data=session.get_session_info(), message="获取会话信息成功")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取会话信息失败: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取会话信息失败: {e}") from e


@router.post("/sessions/{session_id}/reconnect", response_model=SuccessResponse, summary="重连指定的CLI会话")
async def reconnect_session(
    session_id: str,
    dynamic_password: str | None = None,
    operation_context: OperationContext = Depends(require_permission(Permissions.CLI_ACCESS)),
    cli_service: CLISessionService = Depends(get_cli_service),
):
    """重连指定的CLI会话"""
    try:
        success = await cli_service.reconnect_session(
            session_id=session_id, operation_context=operation_context, dynamic_password=dynamic_password
        )

        if not success:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="重连失败")

        return SuccessResponse(message=f"会话 {session_id} 重连成功")
    except BusinessException as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e
    except Exception as e:
        logger.error(f"重连CLI会话失败: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"重连失败: {e}") from e
