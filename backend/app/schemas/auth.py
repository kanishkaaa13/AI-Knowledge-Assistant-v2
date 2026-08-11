from pydantic import BaseModel, EmailStr

from app.schemas.common import PasswordFieldMixin
from app.schemas.user import UserRead


class UserLogin(PasswordFieldMixin, BaseModel):
    email: EmailStr


class AuthResponse(BaseModel):
    user: UserRead
    access_token: str | None = None
    token_type: str = "bearer"
    message: str
