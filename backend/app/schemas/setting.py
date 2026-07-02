import uuid

from pydantic import Field

from app.schemas.common import ORMBaseSchema, TimestampSchema


class SettingBase(ORMBaseSchema):
    theme: str = Field(default="system", min_length=1, max_length=20)
    preferred_model: str = Field(default="gpt-4o-mini", min_length=1, max_length=100)
    memory_enabled: bool = True


class SettingCreate(SettingBase):
    user_id: uuid.UUID


class SettingUpdate(ORMBaseSchema):
    theme: str | None = Field(default=None, min_length=1, max_length=20)
    preferred_model: str | None = Field(default=None, min_length=1, max_length=100)
    memory_enabled: bool | None = None


class SettingRead(SettingBase, TimestampSchema):
    user_id: uuid.UUID
