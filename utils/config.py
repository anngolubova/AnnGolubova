from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


def _parse_csv(raw_value: str | None) -> list[str]:
    if not raw_value:
        return []
    return [item.strip() for item in raw_value.split(",") if item.strip()]


def _parse_int_csv(raw_value: str | None) -> list[int]:
    result: list[int] = []
    for item in _parse_csv(raw_value):
        result.append(int(item))
    return result


@dataclass(slots=True)
class Settings:
    bot_tokens: list[str]
    constructor_bot_token: str | None
    admin_chat_id: int | None
    bot_admin_chat_ids: list[int]
    database_url: str
    redis_url: str
    log_level: str
    managed_bots_sync_interval_seconds: int

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv()

        bot_tokens = _parse_csv(os.getenv("BOT_TOKENS"))
        constructor_bot_token = os.getenv("CONSTRUCTOR_BOT_TOKEN")
        if not bot_tokens and not constructor_bot_token:
            raise ValueError(
                "Set BOT_TOKENS (managed bots) and/or CONSTRUCTOR_BOT_TOKEN (admin cabinet bot)."
            )

        admin_chat_id_raw = os.getenv("ADMIN_CHAT_ID")
        admin_chat_id = int(admin_chat_id_raw) if admin_chat_id_raw else None

        return cls(
            bot_tokens=bot_tokens,
            constructor_bot_token=constructor_bot_token.strip() if constructor_bot_token else None,
            admin_chat_id=admin_chat_id,
            bot_admin_chat_ids=_parse_int_csv(os.getenv("BOT_ADMIN_CHAT_IDS")),
            database_url=os.getenv(
                "DATABASE_URL",
                "sqlite+aiosqlite:///./data/feedback_bot.db",
            ),
            redis_url=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            managed_bots_sync_interval_seconds=int(
                os.getenv("MANAGED_BOTS_SYNC_INTERVAL_SECONDS", "8")
            ),
        )
