"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: auth.py
@DateTime: 2025/07/08
@Docs: 认证相关API端点
"""

from fastapi import APIRouter, Depends, Request
from fastapi.security import OAuth2PasswordRequestForm
from fastapi_throttle import RateLimiter

from app.models.user import User
from app.schemas.auth import (
    ChangePasswordRequest,
    ChangePasswordResponse,
    LoginRequest,
    LogoutResponse,
    ProfileResponse,
    RefreshTokenRequest,
    UpdateProfileRequest,
    UpdateProfileResponse,
)
from app.schemas.base import SuccessResponse, TokenResponse
from app.services.auth import AuthService
from app.utils.deps import get_auth_service, get_current_active_user

router = APIRouter(prefix="/auth", tags=["认证管理"])
login_limiter = RateLimiter(times=3, seconds=10)  # 限制登录请求频率为每10秒3次


@router.post("/login", response_model=TokenResponse, summary="用户登录", dependencies=[Depends(login_limiter)])
async def login(
    login_data: LoginRequest,
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
):
    """用户登录接口"""
    user_agent = request.headers.get("user-agent", "unknown")
    client_ip = request.client.host if request.client else "unknown"
    result = await auth_service.login(login_data, client_ip, user_agent)
    return result.data


@router.post("/login/form", response_model=TokenResponse, summary="表单登录", dependencies=[Depends(login_limiter)])
async def login_form(
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
    form_data: OAuth2PasswordRequestForm = Depends(),
):
    """OAuth2 表单登录接口"""
    user_agent = request.headers.get("user-agent", "unknown")
    client_ip = request.client.host if request.client else "unknown"
    login_data = LoginRequest(username=form_data.username, password=form_data.password)
    result = await auth_service.login(login_data, client_ip, user_agent)
    return result.data


@router.post("/logout", response_model=LogoutResponse, summary="用户登出")
async def logout(
    auth_service: AuthService = Depends(get_auth_service),
    current_user: User = Depends(get_current_active_user),
):
    """用户登出接口"""
    await auth_service.logout(current_user.id)
    return SuccessResponse()


@router.post("/refresh", response_model=TokenResponse, summary="刷新令牌")
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """刷新访问令牌"""
    result = await auth_service.refresh_token(refresh_data.refresh_token)
    return result.data


@router.get("/profile", response_model=ProfileResponse, summary="获取用户信息")
async def get_profile(
    auth_service: AuthService = Depends(get_auth_service),
    current_user: User = Depends(get_current_active_user),
):
    """获取当前用户详细信息"""
    return await auth_service.get_current_user_profile(current_user)


@router.put("/profile", response_model=UpdateProfileResponse, summary="更新用户信息")
async def update_profile(
    profile_data: UpdateProfileRequest,
    auth_service: AuthService = Depends(get_auth_service),
    current_user: User = Depends(get_current_active_user),
):
    """更新当前用户信息"""
    return await auth_service.update_current_user_profile(current_user, profile_data)


@router.put("/password", response_model=ChangePasswordResponse, summary="修改密码")
async def change_password(
    password_data: ChangePasswordRequest,
    auth_service: AuthService = Depends(get_auth_service),
    current_user: User = Depends(get_current_active_user),
):
    """修改当前用户密码"""
    await auth_service.change_password(current_user, password_data)
    return SuccessResponse()
