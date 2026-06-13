# MVP Plan

## Phase 1: Skeleton

- Create the FastAPI app
- Add SQLAlchemy models
- Add local SQLite support
- Add Jinja templates and mobile-first CSS
- Add the public routes
- Add the admin route
- Add a Telegram bot skeleton

## Phase 2: Local Content Flow

- Save employee-submitted drops as drafts
- Add category selection
- Add optional price capture
- Add optional description capture
- Add draft listing in admin

## Phase 3: Publishing Flow

- Publish a set of drafts as one batch
- Mark published_at on the selected drops
- Send one Telegram message for the batch
- Keep unpublished drafts hidden from customers

## Phase 4: Admin Maintenance

- Edit drops
- Archive drops
- Delete drops if needed
- Edit categories
- Edit store settings

## Phase 5: Later Enhancements

- Migrate from SQLite to PostgreSQL
- Add admin authentication
- Add photo storage improvements
- Add moderation helpers for Telegram
- Add analytics if the business needs it

