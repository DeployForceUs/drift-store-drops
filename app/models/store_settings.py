from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class StoreSettings(Base):
    """Simple singleton table for store contact and hours."""

    __tablename__ = "store_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    store_name: Mapped[str] = mapped_column(String(120), nullable=False, default="Drift Store")
    phone: Mapped[str] = mapped_column(String(50), nullable=False, default="")
    address: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    timezone: Mapped[str] = mapped_column(String(64), nullable=False, default="America/New_York")
    open_time: Mapped[str] = mapped_column(String(5), nullable=False, default="10:00")
    close_time: Mapped[str] = mapped_column(String(5), nullable=False, default="18:00")
    map_url: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

