from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_serializer

from app.services.s3_service import build_presigned_avatar_url


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    avatar_url: str | None = None
    created_at: datetime
    updated_at: datetime

    @field_serializer("avatar_url")
    def serialize_avatar_url(self, value: str | None) -> str | None:
        # Stored value is an S3 key (or legacy full URL); expose a browser-openable URL.
        return build_presigned_avatar_url(value)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
