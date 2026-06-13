# Architecture

## Overview

The app is intentionally simple.
One FastAPI application serves the website and admin views.
SQLAlchemy handles persistence.
A separate Telegram bot process can collect employee submissions and send subscriber alerts.

## Components

- `app/main.py` - FastAPI app and routes
- `app/models/` - database models
- `app/services/` - data helpers and notification stubs
- `app/bot/telegram_bot.py` - Telegram bot skeleton
- `app/templates/` - Jinja2 HTML templates
- `app/static/` - CSS

## Request Flow

### Customer browsing

1. Customer opens `/` or `/latest`
2. FastAPI loads drops and categories from SQLite
3. Jinja2 renders HTML
4. Customer taps a card to open `/drop/{id}`
5. The detail page shows call and directions actions

### Employee intake

1. Employee sends a photo to Telegram
2. Bot collects category, optional price, and optional description
3. A new drop is stored as `draft`
4. Admin reviews the draft later

### Batch publish

1. Admin selects drafts
2. App marks them `published`
3. App assigns a shared batch id
4. Notification service sends one batch alert to subscribers

## Data Storage

- SQLite for local development
- PostgreSQL later without changing the model shape too much

## Design Choices

- Jinja2 instead of a frontend framework
- Plain HTML and CSS for speed and simplicity
- A single store settings row for the MVP
- Daily open/close hours instead of a complex scheduling engine

## Known Limits

- No authentication yet
- No upload pipeline yet for photo blobs
- No real Telegram handlers yet
- No batch management UI yet
- No customer-side sold or hold state

