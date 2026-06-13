from dataclasses import dataclass


@dataclass
class TelegramBotConfig:
    """Minimal configuration for the Telegram bot skeleton."""

    token: str


class TelegramDropBot:
    """Skeleton for the Telegram bot that will collect new drops from employees."""

    def __init__(self, config: TelegramBotConfig) -> None:
        self.config = config

    def start(self) -> None:
        """Start the bot loop.

        This is intentionally minimal for the MVP skeleton.
        """

        if not self.config.token:
            raise ValueError("Telegram bot token is missing.")

    def handle_photo(self, *args, **kwargs) -> None:
        """Placeholder for the first step of the employee workflow."""

        _ = args
        _ = kwargs

    def handle_category(self, *args, **kwargs) -> None:
        """Placeholder for category capture after the photo is received."""

        _ = args
        _ = kwargs

    def handle_price(self, *args, **kwargs) -> None:
        """Placeholder for optional price capture."""

        _ = args
        _ = kwargs

    def handle_description(self, *args, **kwargs) -> None:
        """Placeholder for optional description capture."""

        _ = args
        _ = kwargs

