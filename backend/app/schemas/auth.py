from uuid import UUID
from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    organization_name: str = Field(..., min_length=1, max_length=255)
    timezone: str = "Asia/Singapore"
    language: str = "zh"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    id: UUID
    name: str
    email: str
    organization_id: UUID
    avatar_url: str | None = None
    language: str
    timezone: str
    role_name: str | None = None

    model_config = {"from_attributes": True}
