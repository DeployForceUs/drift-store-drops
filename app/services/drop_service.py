import json
from datetime import datetime, timedelta
from typing import Iterable

from sqlalchemy import func
from sqlalchemy.orm import joinedload, Session

from app.models.category import Category
from app.models.drop import Drop, DropStatus
from app.models.store_settings import StoreSettings

DEFAULT_CATEGORIES = [
    "Furniture",
    "Beds",
    "Dressers",
    "Tables",
    "Chairs",
    "Decor",
    "Electronics",
    "Other",
]

LEGACY_CLOTHING_CATEGORIES = [
    "Women's Tops",
    "Men's Tees",
    "Denim",
    "Outerwear",
    "Shoes",
    "Accessories",
    "Home & Decor",
]


def slugify(value: str) -> str:
    """Create a simple slug from a category name."""

    slug = value.strip().lower().replace("&", " and ")
    chars = []
    for char in slug:
        if char.isalnum():
            chars.append(char)
        elif chars and chars[-1] != "-":
            chars.append("-")
    return "".join(chars).strip("-")


def ensure_seed_data(db: Session, settings_defaults: dict[str, str]) -> None:
    """Create minimal seed data for a fresh local database."""

    if db.query(Category).count() == 0:
        for index, name in enumerate(DEFAULT_CATEGORIES):
            db.add(Category(name=name, slug=slugify(name), sort_order=index))

    if db.query(StoreSettings).count() == 0:
        db.add(
            StoreSettings(
                store_name=settings_defaults["store_name"],
                phone=settings_defaults["store_phone"],
                address=settings_defaults["store_address"],
                timezone=settings_defaults["store_timezone"],
                open_time=settings_defaults["store_open_time"],
                close_time=settings_defaults["store_close_time"],
                map_url=settings_defaults["store_map_url"],
            )
        )

    db.commit()


def ensure_default_categories(db: Session) -> int:
    """Seed thrift defaults and disable legacy clothing categories."""

    existing_categories = db.query(Category).all()
    existing_by_slug = {category.slug: category for category in existing_categories}
    existing_by_name = {category.name.lower(): category for category in existing_categories}

    inserted = 0
    for index, name in enumerate(DEFAULT_CATEGORIES):
        slug = slugify(name)
        category = existing_by_slug.get(slug) or existing_by_name.get(name.lower())
        if category is None:
            db.add(Category(name=name, slug=slug, sort_order=index, is_active=True))
            inserted += 1
            continue
        category.name = name
        category.slug = slug
        category.sort_order = index
        category.is_active = True

    for category in existing_categories:
        if category.name in LEGACY_CLOTHING_CATEGORIES:
            category.is_active = False

    db.commit()
    return inserted


def seed_sample_drops(db: Session) -> int:
    """Seed a small set of published demo drops for local development."""

    if db.query(Drop).filter(Drop.status == DropStatus.published).count() > 0:
        return 0

    categories = {category.slug: category for category in list_categories(db, active_only=False)}
    now = datetime.utcnow()
    sample_drops = [
        {
            "slug": "furniture",
            "price": 180.0,
            "description": "Solid wood sideboard with clean lines and a warm oak finish.",
            "photo_text": "Wood Sideboard",
            "days_ago": 0,
            "minutes_ago": 35,
        },
        {
            "slug": "beds",
            "price": 240.0,
            "description": "Queen bed frame with slatted support and light neutral fabric.",
            "photo_text": "Queen Bed",
            "days_ago": 0,
            "minutes_ago": 50,
        },
        {
            "slug": "tables",
            "price": 95.0,
            "description": "Round accent table with tapered legs and smooth top.",
            "photo_text": "Accent Table",
            "days_ago": 1,
            "minutes_ago": 20,
        },
        {
            "slug": "chairs",
            "price": 65.0,
            "description": "Upholstered dining chair with compact footprint.",
            "photo_text": "Dining Chair",
            "days_ago": 1,
            "minutes_ago": 45,
        },
        {
            "slug": "decor",
            "price": 24.0,
            "description": "Ceramic table lamp with soft neutral shade.",
            "photo_text": "Ceramic Lamp",
            "days_ago": 2,
            "minutes_ago": 15,
        },
        {
            "slug": "electronics",
            "price": 120.0,
            "description": "Compact stereo receiver with Bluetooth support.",
            "photo_text": "Stereo Receiver",
            "days_ago": 2,
            "minutes_ago": 40,
        },
        {
            "slug": "other",
            "price": 48.0,
            "description": "Miscellaneous home find ready for the next room.",
            "photo_text": "Misc Home Item",
            "days_ago": 3,
            "minutes_ago": 30,
        },
    ]

    batch_map: dict[int, int] = {}
    inserted = 0
    for index, item in enumerate(sample_drops, start=1):
        category = categories.get(item["slug"])
        if category is None:
            continue

        batch_key = 1 if index <= 4 else 2
        if batch_key not in batch_map:
            batch_map[batch_key] = int((now - timedelta(days=batch_key)).timestamp())

        published_at = now - timedelta(days=item["days_ago"], minutes=item["minutes_ago"])
        db.add(
            Drop(
                category_id=category.id,
                status=DropStatus.published,
                image_url=(
                    "https://placehold.co/1200x1200/f4f1ea/1f2421?text="
                    + item["photo_text"].replace(" ", "+")
                ),
                price=item["price"],
                description=item["description"],
                batch_id=batch_map[batch_key],
                published_at=published_at,
            )
        )
        inserted += 1

    db.commit()
    return inserted


def get_drop_for_edit(db: Session, drop_id: int) -> Drop | None:
    """Load one drop for admin editing."""

    return db.query(Drop).options(joinedload(Drop.category)).filter(Drop.id == drop_id).first()


def list_drops_by_status(db: Session, status: DropStatus) -> list[Drop]:
    """Load drops for a single admin section."""

    return (
        db.query(Drop)
        .options(joinedload(Drop.category))
        .filter(Drop.status == status)
        .order_by(Drop.created_at.desc())
        .all()
    )


def create_drop(
    db: Session,
    *,
    category_id: int,
    title: str | None,
    image_url: str | None,
    photo_urls: list[str] | None = None,
    price: float | None,
    description: str | None,
) -> Drop:
    """Create a new draft drop."""

    cover_photo_url = photo_urls[0] if photo_urls else image_url
    drop = Drop(
        category_id=category_id,
        title=title,
        status=DropStatus.draft,
        image_url=cover_photo_url,
        photo_paths_json=json.dumps(photo_urls) if photo_urls else None,
        price=price,
        description=description,
    )
    db.add(drop)
    db.commit()
    db.refresh(drop)
    return drop


def update_drop(
    db: Session,
    drop: Drop,
    *,
    category_id: int,
    title: str | None,
    image_url: str | None,
    photo_urls: list[str] | None = None,
    price: float | None,
    description: str | None,
) -> Drop:
    """Update the editable fields on a drop."""

    drop.category_id = category_id
    drop.title = title
    if photo_urls is not None:
        drop.image_url = photo_urls[0] if photo_urls else None
        drop.photo_paths_json = json.dumps(photo_urls) if photo_urls else None
    elif image_url is not None:
        drop.image_url = image_url
    drop.price = price
    drop.description = description
    db.commit()
    db.refresh(drop)
    return drop


def generate_owner_title(category_name: str, price: float | None) -> str:
    """Build a simple title for the owner intake flow."""

    if price is None:
        return "New thrift item"
    formatted = f"${price:.0f}" if price.is_integer() else f"${price:.2f}"
    return f"{category_name} {formatted}"


def publish_drop(db: Session, drop: Drop) -> Drop:
    """Publish one drop."""

    create_published_batch(db, [drop])
    db.refresh(drop)
    return drop


def publish_all_drafts(db: Session) -> int:
    """Publish all draft drops in one batch."""

    drafts = list_drops_by_status(db, DropStatus.draft)
    if not drafts:
        return 0
    create_published_batch(db, drafts)
    return len(drafts)


def archive_drop(db: Session, drop: Drop) -> Drop:
    """Archive one drop."""

    drop.status = DropStatus.archived
    drop.archived_at = datetime.utcnow()
    db.commit()
    db.refresh(drop)
    return drop


def delete_drop(db: Session, drop: Drop) -> None:
    """Delete one drop from the database."""

    db.delete(drop)
    db.commit()


def list_categories(db: Session, active_only: bool = True) -> list[Category]:
    query = db.query(Category)
    if active_only:
        query = query.filter(Category.is_active.is_(True))
    return query.order_by(Category.sort_order.asc(), Category.name.asc()).all()


def get_category_by_slug(db: Session, slug: str, *, active_only: bool = True) -> Category | None:
    query = db.query(Category).filter(Category.slug == slug)
    if active_only:
        query = query.filter(Category.is_active.is_(True))
    return query.first()


def get_category_by_id(db: Session, category_id: int) -> Category | None:
    return db.query(Category).filter(Category.id == category_id).first()


def get_category_by_name(db: Session, name: str) -> Category | None:
    return db.query(Category).filter(Category.name == name).first()


def next_category_sort_order(db: Session) -> int:
    max_sort_order = db.query(func.max(Category.sort_order)).scalar()
    return int(max_sort_order or 0) + 1


def create_category(db: Session, *, name: str) -> Category:
    slug = slugify(name)
    if get_category_by_name(db, name) is not None:
        raise ValueError("Category name already exists")
    if db.query(Category).filter(Category.slug == slug).first() is not None:
        raise ValueError("Category slug already exists")

    category = Category(name=name, slug=slug, sort_order=next_category_sort_order(db), is_active=True)
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


def update_category(db: Session, category: Category, *, name: str) -> Category:
    existing = get_category_by_name(db, name)
    if existing is not None and existing.id != category.id:
        raise ValueError("Category name already exists")

    category.name = name
    db.commit()
    db.refresh(category)
    return category


def set_category_active(db: Session, category: Category, *, is_active: bool) -> Category:
    category.is_active = is_active
    db.commit()
    db.refresh(category)
    return category


def list_latest_published_drops(db: Session, limit: int = 12) -> list[Drop]:
    return list_visible_drops(db, limit=limit)


def list_category_published_drops(db: Session, category_id: int, limit: int = 24) -> list[Drop]:
    return list_visible_drops(db, limit=limit, category_id=category_id)


def get_drop(db: Session, drop_id: int) -> Drop | None:
    return db.query(Drop).options(joinedload(Drop.category)).filter(Drop.id == drop_id).first()


def list_drafts(db: Session, limit: int = 24) -> list[Drop]:
    return (
        db.query(Drop)
        .options(joinedload(Drop.category))
        .filter(Drop.status == DropStatus.draft)
        .order_by(Drop.created_at.desc())
        .limit(limit)
        .all()
    )


def count_drops_by_status(db: Session) -> dict[str, int]:
    counts = {
        row.status.value: row.total
        for row in db.query(Drop.status.label("status"), func.count(Drop.id).label("total"))
        .group_by(Drop.status)
        .all()
    }
    return {
        "draft": counts.get("draft", 0),
        "published": counts.get("published", 0),
        "sold": counts.get("sold", 0),
        "archived": counts.get("archived", 0),
    }


def list_visible_drops(db: Session, limit: int | None = None, category_id: int | None = None) -> list[Drop]:
    """Load items visible on the public site."""

    query = (
        db.query(Drop)
        .options(joinedload(Drop.category))
        .filter(Drop.status.in_([DropStatus.published, DropStatus.sold]))
        .order_by(Drop.published_at.desc().nullslast(), Drop.created_at.desc())
    )
    if category_id is not None:
        query = query.filter(Drop.category_id == category_id)
    if limit is not None:
        query = query.limit(limit)
    return query.all()


def mark_sold_drop(db: Session, drop: Drop) -> Drop:
    """Mark one drop as sold."""

    drop.status = DropStatus.sold
    db.commit()
    db.refresh(drop)
    return drop


def reset_demo_data(db: Session) -> dict[str, int]:
    """Reset local demo content while keeping the store settings row."""

    drop_count = db.query(Drop).delete()
    category_count = db.query(Category).delete()
    db.commit()
    ensure_default_categories(db)
    return {"drops_deleted": drop_count, "categories_deleted": category_count}


def create_published_batch(db: Session, drops: Iterable[Drop]) -> int:
    """Assign a simple shared batch id to a group of drops."""

    batch_id = int(datetime.utcnow().timestamp())
    for drop in drops:
        drop.batch_id = batch_id
        drop.status = DropStatus.published
        drop.published_at = datetime.utcnow()
    db.commit()
    return batch_id
