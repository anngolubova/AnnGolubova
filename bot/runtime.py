from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


@dataclass(slots=True)
class BotRuntime:
    db_bot_id: int
    token: str
    username: str | None
    admin_chat_id: int


@dataclass(slots=True)
class ServiceContainer:
    session_factory: async_sessionmaker[AsyncSession]
    runtime: BotRuntime
