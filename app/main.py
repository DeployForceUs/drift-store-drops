import sqlite3
from pathlib import Path
from uuid import uuid4
from datetime import datetime, time
from zoneinfo import ZoneInfo

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import SessionLocal, engine, get_db
from app.models import Base, DropStatus
from app.models.store_settings import StoreSettings
from app.services.drop_service import (
    count_drops_by_status,
    create_drop,
    create_category,
    delete_drop,
    archive_drop,
    ensure_seed_data,
    ensure_default_categories,
    get_category_by_slug,
    get_category_by_id,
    slugify,
    get_drop_for_edit,
    generate_owner_title,
    mark_sold_drop,
    list_drops_by_status,
    list_categories,
    list_category_published_drops,
    list_latest_published_drops,
    publish_all_drafts,
    publish_drop,
    reset_demo_data,
    set_category_active,
    update_category,
    update_drop,
)

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"
UPLOADS_DIR = BASE_DIR.parent / "uploads"

app = FastAPI(title=settings.app_name)
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")


def get_store_settings(db: Session) -> StoreSettings:
    """Return the single store settings row, creating a fallback if needed."""

    store_settings = db.query(StoreSettings).first()
    if store_settings is None:
        store_settings = StoreSettings(
            store_name=settings.store_name,
            phone=settings.store_phone,
            address=settings.store_address,
            timezone=settings.store_timezone,
            open_time=settings.store_open_time,
            close_time=settings.store_close_time,
            map_url=settings.store_map_url,
        )
        db.add(store_settings)
        db.commit()
        db.refresh(store_settings)
    return store_settings


def is_store_open(store_settings: StoreSettings) -> bool:
    """Check whether the store is open using simple daily hours."""

    try:
        tz = ZoneInfo(store_settings.timezone)
    except Exception:
        tz = ZoneInfo("America/New_York")

    now = datetime.now(tz).time()
    open_hour, open_minute = [int(part) for part in store_settings.open_time.split(":")]
    close_hour, close_minute = [int(part) for part in store_settings.close_time.split(":")]
    open_time = time(open_hour, open_minute)
    close_time = time(close_hour, close_minute)

    if open_time <= close_time:
        return open_time <= now <= close_time
    return now >= open_time or now <= close_time


def build_maps_url(store_settings: StoreSettings) -> str:
    """Prefer the configured maps URL, then fall back to a Google Maps search link."""

    if store_settings.map_url:
        return store_settings.map_url
    address = store_settings.address.replace(" ", "+")
    return f"https://www.google.com/maps/search/?api=1&query={address}"


def admin_context(request: Request, db: Session) -> dict:
    """Build the common context for admin pages."""

    store_settings = get_store_settings(db)
    return {
        "request": request,
        "store_settings": store_settings,
        "draft_drops": list_drops_by_status(db, DropStatus.draft),
        "published_drops": list_drops_by_status(db, DropStatus.published),
        "sold_drops": list_drops_by_status(db, DropStatus.sold),
        "archived_drops": list_drops_by_status(db, DropStatus.archived),
        "counts": count_drops_by_status(db),
    }


def parse_optional_float(value: str | None) -> float | None:
    """Convert a form field to a float when present."""

    if value is None:
        return None
    text = value.strip()
    if not text:
        return None
    return float(text)


def parse_optional_text(value: str | None) -> str | None:
    """Normalize blank form fields to None."""

    if value is None:
        return None
    text = value.strip()
    return text or None


def redirect(url: str) -> RedirectResponse:
    """Redirect after POST to avoid resubmission."""

    return RedirectResponse(url=url, status_code=303)


def ensure_drop_title_column() -> None:
    """Add the title column to older local SQLite databases if needed."""

    if not settings.database_url.startswith("sqlite:///./"):
        return

    database_path = settings.database_url.removeprefix("sqlite:///./")
    conn = sqlite3.connect(database_path)
    try:
        columns = {row[1] for row in conn.execute("PRAGMA table_info(drops)").fetchall()}
        if "title" not in columns:
            conn.execute("ALTER TABLE drops ADD COLUMN title VARCHAR(200)")
            conn.commit()
    finally:
        conn.close()


def ensure_drop_photo_paths_column() -> None:
    """Add the photo paths column to older local SQLite databases if needed."""

    if not settings.database_url.startswith("sqlite:///./"):
        return

    database_path = settings.database_url.removeprefix("sqlite:///./")
    conn = sqlite3.connect(database_path)
    try:
        columns = {row[1] for row in conn.execute("PRAGMA table_info(drops)").fetchall()}
        if "photo_paths_json" not in columns:
            conn.execute("ALTER TABLE drops ADD COLUMN photo_paths_json TEXT")
            conn.commit()
    finally:
        conn.close()


def ensure_category_updated_at_column() -> None:
    """Add the category updated_at column to older local SQLite databases if needed."""

    if not settings.database_url.startswith("sqlite:///./"):
        return

    database_path = settings.database_url.removeprefix("sqlite:///./")
    conn = sqlite3.connect(database_path)
    try:
        columns = {row[1] for row in conn.execute("PRAGMA table_info(categories)").fetchall()}
        if "updated_at" not in columns:
            conn.execute("ALTER TABLE categories ADD COLUMN updated_at DATETIME")
        conn.execute(
            "UPDATE categories SET updated_at = COALESCE(updated_at, created_at)"
        )
        conn.commit()
    finally:
        conn.close()


def build_form_categories(db: Session, current_category_id: int | None = None):
    """Return active categories, keeping a disabled current category available for edits."""

    categories = list_categories(db, active_only=True)
    if current_category_id is None:
        return categories

    if any(category.id == current_category_id for category in categories):
        return categories

    current_category = get_category_by_id(db, current_category_id)
    if current_category is None:
        return categories

    return categories + [current_category]


def get_or_create_category(db: Session, *, category_id: int | None, category_name: str | None):
    """Return an existing category or create one inline from the form."""

    if category_name:
        name = category_name.strip()
        if not name:
            raise HTTPException(status_code=400, detail="Category name is required")
        try:
            return create_category(db, name=name)
        except ValueError as exc:
            message = str(exc)
            if "exists" in message:
                normalized_slug = slugify(name)
                existing = next(
                    (
                        item
                        for item in list_categories(db, active_only=False)
                        if item.name.lower() == name.lower() or item.slug == normalized_slug
                    ),
                    None,
                )
                if existing is not None:
                    if not existing.is_active:
                        set_category_active(db, existing, is_active=True)
                    return existing
            raise HTTPException(status_code=400, detail=message) from exc

    if category_id is None:
        raise HTTPException(status_code=400, detail="Invalid category")

    category = next((item for item in build_form_categories(db) if item.id == category_id), None)
    if category is None:
        category = get_category_by_id(db, category_id)
    if category is None:
        raise HTTPException(status_code=400, detail="Invalid category")
    return category


async def save_uploaded_photos(form_data, *, required: bool) -> list[str] | None:
    """Validate uploaded images and store them under /uploads."""

    uploaded_files = [
        file
        for file in form_data.getlist("photos")
        if getattr(file, "filename", None) and hasattr(file, "read")
    ]
    if not uploaded_files:
        if required:
            raise HTTPException(status_code=400, detail="Upload at least one photo")
        return None

    if len(uploaded_files) > 5:
        raise HTTPException(status_code=400, detail="Upload up to 5 photos")

    for file in uploaded_files:
        content_type = file.content_type or ""
        if not content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="Photos must be image files")

    photo_urls: list[str] = []
    for file in uploaded_files:
        suffix = Path(file.filename).suffix.lower() or ".jpg"
        filename = f"{uuid4().hex}{suffix}"
        destination = UPLOADS_DIR / filename
        contents = await file.read()
        if not contents:
            raise HTTPException(status_code=400, detail="Empty photo upload")
        destination.write_bytes(contents)
        photo_urls.append(f"/uploads/{filename}")

    return photo_urls


@app.on_event("startup")
def startup_event() -> None:
    """Create tables and seed a few local defaults."""

    Base.metadata.create_all(bind=engine)
    ensure_drop_title_column()
    ensure_drop_photo_paths_column()
    ensure_category_updated_at_column()
    db = SessionLocal()
    try:
        ensure_default_categories(db)
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
    finally:
        db.close()


@app.get("/", response_class=HTMLResponse)
def home(request: Request, db: Session = Depends(get_db)):
    """Homepage that highlights latest arrivals."""

    store_settings = get_store_settings(db)
    context = {
        "store_settings": store_settings,
        "categories": list_categories(db),
        "drops": list_latest_published_drops(db, limit=6),
        "is_open": is_store_open(store_settings),
        "maps_url": build_maps_url(store_settings),
    }
    return templates.TemplateResponse(request, "index.html", context)


@app.get("/latest", response_class=HTMLResponse)
def latest(request: Request, db: Session = Depends(get_db)):
    """Latest published drops."""

    store_settings = get_store_settings(db)
    context = {
        "store_settings": store_settings,
        "categories": list_categories(db),
        "drops": list_latest_published_drops(db),
        "is_open": is_store_open(store_settings),
        "maps_url": build_maps_url(store_settings),
    }
    return templates.TemplateResponse(request, "latest.html", context)


@app.get("/category/{slug}", response_class=HTMLResponse)
def category_detail(slug: str, request: Request, db: Session = Depends(get_db)):
    """Browse published drops in a category."""

    category = get_category_by_slug(db, slug, active_only=False)
    if category is None:
        raise HTTPException(status_code=404, detail="Category not found")

    store_settings = get_store_settings(db)
    context = {
        "store_settings": store_settings,
        "categories": list_categories(db),
        "category": category,
        "drops": list_category_published_drops(db, category.id),
        "is_open": is_store_open(store_settings),
        "maps_url": build_maps_url(store_settings),
    }
    return templates.TemplateResponse(request, "category.html", context)


@app.get("/drop/{drop_id}", response_class=HTMLResponse)
def drop_detail(drop_id: int, request: Request, db: Session = Depends(get_db)):
    """View one drop card with store contact actions."""

    drop = get_drop_for_edit(db, drop_id)
    if drop is None:
        raise HTTPException(status_code=404, detail="Drop not found")

    store_settings = get_store_settings(db)
    context = {
        "store_settings": store_settings,
        "categories": list_categories(db),
        "drop": drop,
        "is_open": is_store_open(store_settings),
        "maps_url": build_maps_url(store_settings),
    }
    return templates.TemplateResponse(request, "drop.html", context)


@app.get("/admin", response_class=HTMLResponse)
def admin_dashboard(request: Request, db: Session = Depends(get_db)):
    """Simple local admin dashboard for drafts and store setup."""

    return templates.TemplateResponse(request, "admin.html", admin_context(request, db))


@app.post("/admin/categories/new")
async def admin_create_category(request: Request, db: Session = Depends(get_db)):
    """Create a new category for the store."""

    form = await request.form()
    name = parse_optional_text(form.get("name"))
    if not name:
        raise HTTPException(status_code=400, detail="Category name is required")

    existing = next((item for item in list_categories(db, active_only=False) if item.name.lower() == name.lower()), None)
    if existing is not None:
        if not existing.is_active:
            set_category_active(db, existing, is_active=True)
        category = existing
    else:
        try:
            category = create_category(db, name=name)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    wants_json = "application/json" in (request.headers.get("accept") or "") or request.headers.get("x-requested-with") == "fetch"
    if wants_json:
        return JSONResponse(
            {
                "id": category.id,
                "name": category.name,
                "slug": category.slug,
                "is_active": category.is_active,
            }
        )
    return redirect("/admin")


@app.post("/admin/categories/{category_id}/rename")
async def admin_rename_category(category_id: int, request: Request, db: Session = Depends(get_db)):
    """Rename a category and regenerate its slug."""

    category = get_category_by_id(db, category_id)
    if category is None:
        raise HTTPException(status_code=404, detail="Category not found")

    form = await request.form()
    name = parse_optional_text(form.get("name"))
    if not name:
        raise HTTPException(status_code=400, detail="Category name is required")

    try:
        update_category(db, category, name=name)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return redirect("/admin")


@app.post("/admin/categories/{category_id}/toggle")
def admin_toggle_category(category_id: int, db: Session = Depends(get_db)):
    """Enable or disable a category without deleting it."""

    category = get_category_by_id(db, category_id)
    if category is None:
        raise HTTPException(status_code=404, detail="Category not found")

    set_category_active(db, category, is_active=not category.is_active)
    return redirect("/admin")


@app.get("/admin/drops/new", response_class=HTMLResponse)
def admin_new_drop(request: Request, db: Session = Depends(get_db)):
    """Render the create-drop form."""

    context = admin_context(request, db)
    context["drop"] = None
    context["categories"] = build_form_categories(db)
    context["form_action"] = "/admin/drops/new"
    context["page_title"] = "Add Item"
    return templates.TemplateResponse(request, "admin_drop_form.html", context)


@app.post("/admin/drops/new")
async def admin_create_drop(request: Request, db: Session = Depends(get_db)):
    """Create a new draft drop from the admin form."""

    form = await request.form()
    category_value = str(form["category_id"])
    category = None
    if category_value == "__new__":
        category = get_or_create_category(db, category_id=None, category_name=parse_optional_text(form.get("new_category_name")))
    else:
        category = get_or_create_category(db, category_id=int(category_value), category_name=None)
    photo_urls = await save_uploaded_photos(form, required=True)
    price = parse_optional_float(form.get("price"))
    description = parse_optional_text(form.get("description"))

    create_drop(
        db,
        category_id=category.id,
        title=None,
        image_url=None,
        photo_urls=photo_urls,
        price=price,
        description=description,
    )
    return redirect("/admin")


@app.get("/admin/drops/{drop_id}/edit", response_class=HTMLResponse)
def admin_edit_drop(drop_id: int, request: Request, db: Session = Depends(get_db)):
    """Render the edit form for one drop."""

    drop = get_drop_for_edit(db, drop_id)
    if drop is None:
        raise HTTPException(status_code=404, detail="Drop not found")

    context = admin_context(request, db)
    context["drop"] = drop
    context["categories"] = build_form_categories(db, drop.category_id)
    context["form_action"] = f"/admin/drops/{drop_id}/edit"
    context["page_title"] = f"Edit Drop #{drop_id}"
    return templates.TemplateResponse(request, "admin_drop_form.html", context)


@app.post("/admin/drops/{drop_id}/edit")
async def admin_update_drop(drop_id: int, request: Request, db: Session = Depends(get_db)):
    """Save changes to a drop."""

    drop = get_drop_for_edit(db, drop_id)
    if drop is None:
        raise HTTPException(status_code=404, detail="Drop not found")

    form = await request.form()
    category_value = str(form["category_id"])
    if category_value == "__new__":
        category = get_or_create_category(db, category_id=None, category_name=parse_optional_text(form.get("new_category_name")))
    else:
        category = get_or_create_category(db, category_id=int(category_value), category_name=None)
    photo_urls = await save_uploaded_photos(form, required=False)
    price = parse_optional_float(form.get("price"))
    description = parse_optional_text(form.get("description"))

    update_drop(
        db,
        drop,
        category_id=category.id,
        title=drop.title,
        image_url=None,
        photo_urls=photo_urls,
        price=price,
        description=description,
    )
    return redirect("/admin")


@app.post("/admin/drops/{drop_id}/publish")
def admin_publish_drop(drop_id: int, db: Session = Depends(get_db)):
    """Publish one draft or archived drop."""

    drop = get_drop_for_edit(db, drop_id)
    if drop is None:
        raise HTTPException(status_code=404, detail="Drop not found")

    publish_drop(db, drop)
    return redirect("/admin")


@app.post("/admin/drops/{drop_id}/sold")
def admin_mark_sold_drop(drop_id: int, db: Session = Depends(get_db)):
    """Mark one published drop as sold."""

    drop = get_drop_for_edit(db, drop_id)
    if drop is None:
        raise HTTPException(status_code=404, detail="Drop not found")

    mark_sold_drop(db, drop)
    return redirect("/admin")


@app.post("/admin/publish-all-drafts")
def admin_publish_all_drafts(db: Session = Depends(get_db)):
    """Publish every draft in one batch."""

    publish_all_drafts(db)
    return redirect("/admin")


@app.post("/admin/drops/{drop_id}/archive")
def admin_archive_drop(drop_id: int, db: Session = Depends(get_db)):
    """Archive one drop."""

    drop = get_drop_for_edit(db, drop_id)
    if drop is None:
        raise HTTPException(status_code=404, detail="Drop not found")

    archive_drop(db, drop)
    return redirect("/admin")


@app.post("/admin/reset-demo-data")
def admin_reset_demo_data(db: Session = Depends(get_db)):
    """Reset local demo content and re-seed default categories."""

    reset_demo_data(db)
    return redirect("/admin")


@app.post("/admin/drops/{drop_id}/delete")
def admin_delete_drop(drop_id: int, db: Session = Depends(get_db)):
    """Delete one drop."""

    drop = get_drop_for_edit(db, drop_id)
    if drop is None:
        raise HTTPException(status_code=404, detail="Drop not found")

    delete_drop(db, drop)
    return redirect("/admin")


@app.get("/owner/add/{secret}", response_class=HTMLResponse)
def owner_add_item(secret: str, request: Request, db: Session = Depends(get_db)):
    """Tiny mobile-first owner intake page."""

    if secret != settings.owner_secret:
        raise HTTPException(status_code=404, detail="Not found")

    context = {
        "request": request,
        "store_settings": get_store_settings(db),
        "active_categories": list_categories(db, active_only=True),
        "owner_secret": secret,
        "success": request.query_params.get("success") == "1",
    }
    return templates.TemplateResponse(request, "owner_add.html", context)


@app.post("/owner/add/{secret}")
async def owner_create_item(secret: str, request: Request, db: Session = Depends(get_db)):
    """Create and publish an item immediately from the owner intake flow."""

    if secret != settings.owner_secret:
        raise HTTPException(status_code=404, detail="Not found")

    form = await request.form()
    category_value = str(form["category_id"])
    if category_value == "__new__":
        category = get_or_create_category(db, category_id=None, category_name=parse_optional_text(form.get("new_category_name")))
    else:
        category = get_or_create_category(db, category_id=int(category_value), category_name=None)

    photo_urls = await save_uploaded_photos(form, required=True)
    price = parse_optional_float(form.get("price"))
    title = parse_optional_text(form.get("title")) or generate_owner_title(category.name, price)
    description = parse_optional_text(form.get("description"))

    item = create_drop(
        db,
        category_id=category.id,
        title=title,
        image_url=None,
        photo_urls=photo_urls,
        price=price,
        description=description,
    )
    publish_drop(db, item)
    return redirect(f"/owner/add/{secret}?success=1")
