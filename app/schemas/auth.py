from pydantic import BaseModel, EmailStr, Field
from app.schemas.user import UserResponse, UserProfileResponse


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, description="User password (min 8 chars)")


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


class RefreshRequest(BaseModel):
    refresh_token: str = Field(..., min_length=16, description="Cryptographic refresh token")


class RefreshResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LogoutRequest(BaseModel):
    refresh_token: str = Field(..., min_length=16, description="Cryptographic refresh token to revoke")


class LogoutResponse(BaseModel):
    success: bool = True
    message: str = "Logged out successfully"
