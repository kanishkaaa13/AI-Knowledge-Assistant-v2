import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.setting import Setting
from app.repositories.base import BaseRepository


class SettingRepository(BaseRepository[Setting]):
    def __init__(self, db: Session) -> None:
        super().__init__(Setting, db)

    def get_by_user(self, user_id: uuid.UUID) -> Setting | None:
        statement = select(Setting).where(Setting.user_id == user_id)
        return self.db.scalar(statement)
