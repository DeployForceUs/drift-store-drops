from typing import Iterable


class NotificationService:
    """Tiny notification helper for batch publish messages."""

    def build_batch_message(self, store_name: str, batch_count: int) -> str:
        """Build one message for a batch instead of one message per photo."""

        suffix = "item" if batch_count == 1 else "items"
        return f"{store_name} posted {batch_count} new {suffix}. Check the latest arrivals."

    async def send_batch_notification(self, chat_ids: Iterable[str], message: str) -> None:
        """Placeholder for Telegram broadcast delivery."""

        _ = chat_ids
        _ = message
        # Telegram delivery will be wired up after the bot token and subscriber flow are finalized.
        return None

