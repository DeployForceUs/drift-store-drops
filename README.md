# Drift Store Drops

Drift Store Drops is a mobile-first photo catalog for a local thrift/drift store.

This is an MVP skeleton, not an ecommerce app.

What it is:
- A browseable catalog of new arrivals
- A simple admin area for drafts and publishing
- A Telegram workflow for employees to submit new drops
- A Telegram notification flow for subscribers when a batch is published

What it is not:
- No cart
- No checkout
- No online payments
- No shipping
- No customer accounts
- No inventory guarantee
- No Sold/Hold workflow in the MVP

## Tech Stack

- Python
- FastAPI
- Jinja2 templates
- SQLAlchemy
- SQLite for local development
- Telegram bot integration
- Plain HTML and CSS

## Local Setup

1. Create a virtual environment.
2. Install dependencies from `requirements.txt`.
3. Copy `.env.example` to `.env` and fill in values.
4. Run the seed script.
5. Start the app with Uvicorn.

Example:

```bash
python3 -m venv .venv
source .venv/bin/activate
cp .env.example .env
pip install -r requirements.txt
python3 scripts/seed.py
uvicorn app.main:app --reload
```

The seed script creates local tables, adds default store settings, creates 7 editable categories, and inserts sample published drops so the homepage, latest page, category pages, and drop pages show real content right away.

## Project Layout

- `app/main.py` - FastAPI entrypoint and web routes
- `app/models/` - SQLAlchemy models
- `app/services/` - simple data and notification helpers
- `app/bot/` - Telegram bot skeleton
- `app/templates/` - Jinja2 views
- `app/static/` - CSS and other static assets
- `docs/` - product and implementation notes

## MVP Scope

See:
- `docs/PRODUCT_SPEC.md`
- `docs/MVP_PLAN.md`
- `docs/ARCHITECTURE.md`
- `docs/DATABASE.md`
- `docs/CODEX_TASKS.md`
