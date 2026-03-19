from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


@dataclass(slots=True)
class BotRuntime:
    db_bot_id: int
    token: str
    username: str | None
    title: str | None
    welcome_text: str | None
    admin_chat_id: int
    owner_admin_telegram_id: int | None
    is_active: bool


@dataclass(slots=True)
class ServiceContainer:
    session_factory: async_sessionmaker[AsyncSession]
    runtime: BotRuntime
