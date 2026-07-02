from pydantic import BaseModel, EmailStr, Field, field_validator

from app.schemas.user import UserRead


class UserLogin(BaseModel):
    email: EmailStr
    # bcrypt has a 72-byte limit, so we set max_length to 72 characters
    password: str = Field(
        min_length=8,
        max_length=72,
        description="Password must be between 8 and 72 characters"
    )

    @field_validator("password")
    @classmethod
    def validate_password_length(cls, v: str) -> str:
        # Additional check for UTF-8 byte length
        if len(v.encode('utf-8')) > 72:
            raise ValueError(
                "Password exceeds maximum allowed length. "
                "Please use a password with 72 or fewer characters."
            )
        return v


class AuthResponse(BaseModel):
    user: UserRead
    access_token: str | None = None
    token_type: str = "bearer"
    message: str
