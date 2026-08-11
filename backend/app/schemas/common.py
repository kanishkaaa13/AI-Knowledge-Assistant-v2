import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

# bcrypt truncates beyond 72 bytes, so passwords are capped at 72 characters.
BCRYPT_MAX_PASSWORD_BYTES = 72


class ORMBaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class TimestampSchema(ORMBaseSchema):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class PasswordFieldMixin(BaseModel):
    password: str = Field(
        min_length=8,
        max_length=BCRYPT_MAX_PASSWORD_BYTES,
        description=f"Password must be between 8 and {BCRYPT_MAX_PASSWORD_BYTES} characters",
    )

    @field_validator("password")
    @classmethod
    def validate_password_length(cls, value: str) -> str:
        # max_length counts characters, so re-check the UTF-8 byte length
        if len(value.encode("utf-8")) > BCRYPT_MAX_PASSWORD_BYTES:
            raise ValueError(
                "Password exceeds maximum allowed length. "
                f"Please use a password with {BCRYPT_MAX_PASSWORD_BYTES} or fewer characters."
            )
        return value
