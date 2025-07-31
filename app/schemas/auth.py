"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: auth.py
@DateTime: 2025/07/23
@Docs: 认证相关的Pydantic模型
"""

from pydantic import BaseModel, Field, field_validator

from app.schemas.base import AuthRequest, BaseResponse, PasswordUpdateRequest, TokenResponse
from app.schemas.types import ObjectUUID
from app.schemas.user import UserDetailResponse, UserResponse


class TokenPayload(BaseModel):
    """JWT 令牌载荷"""

    sub: ObjectUUID = Field(description="用户ID (subject)")
    username: str | None = Field(default=None, description="用户名")
    is_superuser: bool = Field(default=False, description="是否为超级用户")
    is_active: bool = Field(default=True, description="是否为活跃用户")


class LoginRequest(AuthRequest):
    """用户登录请求"""

    remember_me: bool = Field(default=False, description="记住登录状态")


class LoginResponse(BaseResponse[TokenResponse]):
    """登录响应"""

    pass


class RefreshTokenRequest(BaseModel):
    """刷新令牌请求"""

    refresh_token: str = Field(description="刷新令牌")


class ChangePasswordRequest(PasswordUpdateRequest):
    """修改密码请求"""

    version: int = Field(description="数据版本号，用于乐观锁校验")

    @field_validator("confirm_password")
    @classmethod
    def passwords_match(cls, v, info):
        if "new_password" in info.data and v != info.data["new_password"]:
            raise ValueError("两次输入的密码不一致")
        return v

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v, info):
        if "old_password" in info.data and v == info.data["old_password"]:
            raise ValueError("新密码不能与当前密码相同")
        return v


class ProfileResponse(BaseResponse[UserDetailResponse]):
    """获取个人信息响应"""

    pass


class RefreshTokenResponse(BaseResponse[TokenResponse]):
    """刷新令牌响应"""

    pass


class UpdateProfileResponse(BaseResponse[UserResponse]):
    """更新个人信息响应"""

    pass


class ChangePasswordResponse(BaseResponse[dict]):
    """修改密码响应"""

    pass


class LogoutResponse(BaseResponse[dict]):
    """登出响应"""

    pass


class UpdateProfileRequest(BaseModel):
    """更新个人信息请求"""

    version: int = Field(description="数据版本号，用于乐观锁校验")
    nickname: str | None = Field(default=None, description="昵称", max_length=100)
    avatar_url: str | None = Field(default=None, description="头像URL", max_length=500)
    bio: str | None = Field(default=None, description="个人简介")
