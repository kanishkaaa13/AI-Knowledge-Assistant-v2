import uuid

from pydantic import EmailStr, Field, field_validator

from app.schemas.common import ORMBaseSchema, TimestampSchema


class UserBase(ORMBaseSchema):
    name: str
    email: EmailStr


class UserCreate(UserBase):
    # bcrypt has a 72-byte limit, so we set max_length to 72 characters
    # This ensures UTF-8 encoded passwords won't exceed the limit
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


class UserUpdate(ORMBaseSchema):
    name: str | None = Field(default=None, min_length=2, max_length=255)
    email: EmailStr | None = None


class UserRead(UserBase, TimestampSchema):
    pass


class UserSettingsSummary(ORMBaseSchema):
    user_id: uuid.UUID
    theme: str
    preferred_model: str
    memory_enabled: bool
