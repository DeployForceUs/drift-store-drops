from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class Subscriber(Base):
    """Telegram subscriber who receives batch notifications."""

    __tablename__ = "subscribers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    telegram_chat_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    telegram_username: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

