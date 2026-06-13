# Database

## Tables

### categories

- `id`
- `name`
- `slug`
- `is_active`
- `sort_order`
- `created_at`

### drops

- `id`
- `category_id`
- `status`
- `photo_url`
- `telegram_file_id`
- `price`
- `description`
- `batch_id`
- `published_at`
- `archived_at`
- `created_at`
- `updated_at`

### subscribers

- `id`
- `telegram_chat_id`
- `telegram_username`
- `is_active`
- `created_at`

### store_settings

- `id`
- `store_name`
- `phone`
- `address`
- `timezone`
- `open_time`
- `close_time`
- `map_url`
- `created_at`
- `updated_at`

## Status Model

The `drops.status` column uses these values:

- `draft`
- `published`
- `archived`

## MVP Notes

- Prices are stored as a simple numeric field
- The category relationship is required
- `batch_id` is used to group published drops for one notification
- One `store_settings` row is enough for the MVP

