import json
from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import DateTime, Enum as SAEnum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class DropStatus(str, Enum):
    """Allowed publish states for a drop."""

    draft = "draft"
    published = "published"
    sold = "sold"
    archived = "archived"


class Drop(Base):
    """A single catalog item or post."""

    __tablename__ = "drops"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"), nullable=False, index=True)
    title: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    status: Mapped[DropStatus] = mapped_column(
        SAEnum(DropStatus, name="drop_status"),
        default=DropStatus.draft,
        nullable=False,
        index=True,
    )
    image_url: Mapped[Optional[str]] = mapped_column("photo_url", String(500), nullable=True)
    photo_paths_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    telegram_file_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    batch_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    archived_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    category = relationship("Category", back_populates="drops")

    @property
    def photo_url(self) -> Optional[str]:
        """Backward-compatible alias for older template code."""

        return self.image_url

    @photo_url.setter
    def photo_url(self, value: Optional[str]) -> None:
        self.image_url = value

    @property
    def photo_urls(self) -> list[str]:
        """Return uploaded photo URLs, falling back to the legacy cover image."""

        if self.photo_paths_json:
            try:
                photo_urls = json.loads(self.photo_paths_json)
            except json.JSONDecodeError:
                photo_urls = []
            if isinstance(photo_urls, list):
                cleaned_urls: list[str] = []
                for photo_url in photo_urls:
                    if not photo_url:
                        continue
                    text = str(photo_url).strip()
                    if text:
                        cleaned_urls.append(text)
                return cleaned_urls
        if self.image_url:
            return [self.image_url]
        return []

    @property
    def cover_photo_url(self) -> Optional[str]:
        """Return the first available photo for card and detail views."""

        photo_urls = self.photo_urls
        return photo_urls[0] if photo_urls else None

    @property
    def photo_count(self) -> int:
        """Return the number of available photos."""

        return len(self.photo_urls)
