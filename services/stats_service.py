from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from database.models import Dialog, MessageRecord, User


@dataclass(slots=True)
class StatsSnapshot:
    users_count: int
    dialogs_count: int
    messages_count: int
    messages_last_24h: int


class StatsService:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession], bot_id: int):
        self._session_factory = session_factory
        self._bot_id = bot_id

    async def get_snapshot(self) -> StatsSnapshot:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)

        async with self._session_factory() as session:
            users_stmt = (
                select(func.count(func.distinct(User.id)))
                .join(Dialog, Dialog.user_id == User.id)
                .where(Dialog.bot_id == self._bot_id)
            )
            dialogs_stmt = select(func.count(Dialog.id)).where(Dialog.bot_id == self._bot_id)
            messages_stmt = select(func.count(MessageRecord.id)).where(MessageRecord.bot_id == self._bot_id)
            messages_24h_stmt = select(func.count(MessageRecord.id)).where(
                MessageRecord.bot_id == self._bot_id,
                MessageRecord.created_at >= cutoff,
            )

            users_count = int((await session.execute(users_stmt)).scalar_one() or 0)
            dialogs_count = int((await session.execute(dialogs_stmt)).scalar_one() or 0)
            messages_count = int((await session.execute(messages_stmt)).scalar_one() or 0)
            messages_last_24h = int((await session.execute(messages_24h_stmt)).scalar_one() or 0)

        return StatsSnapshot(
            users_count=users_count,
            dialogs_count=dialogs_count,
            messages_count=messages_count,
            messages_last_24h=messages_last_24h,
        )
