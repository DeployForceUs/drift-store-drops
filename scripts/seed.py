"""Seed local demo data for Drift Store Drops."""

import sqlite3
from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.core.config import settings
from app.db.session import SessionLocal, engine
from app.models import Base
from app.services.drop_service import ensure_seed_data, seed_sample_drops


def ensure_drop_title_column() -> None:
    """Add the title column to older local SQLite databases if needed."""

    database_url = settings.database_url
    if not database_url.startswith("sqlite:///./"):
        return

    database_path = database_url.removeprefix("sqlite:///./")
    conn = sqlite3.connect(database_path)
    try:
        columns = {row[1] for row in conn.execute("PRAGMA table_info(drops)").fetchall()}
        if "title" not in columns:
            conn.execute("ALTER TABLE drops ADD COLUMN title VARCHAR(200)")
            conn.commit()
    finally:
        conn.close()


def main() -> None:
    """Create tables and seed local demo content."""

    Base.metadata.create_all(bind=engine)
    ensure_drop_title_column()
    db = SessionLocal()
    try:
        ensure_seed_data(
            db,
            {
                "store_name": settings.store_name,
                "store_phone": settings.store_phone,
                "store_address": settings.store_address,
                "store_timezone": settings.store_timezone,
                "store_open_time": settings.store_open_time,
                "store_close_time": settings.store_close_time,
                "store_map_url": settings.store_map_url,
            },
        )
        inserted = seed_sample_drops(db)
        print(f"Seed complete. Inserted {inserted} sample drops.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
