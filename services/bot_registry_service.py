from __future__ import annotations

import logging

from aiogram import Bot
from sqlalchemy import not_, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from bot.runtime import BotRuntime
from database.models import BotModel

logger = logging.getLogger(__name__)


class BotRegistryService:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self._session_factory = session_factory

    async def sync_from_tokens(
        self,
        *,
        tokens: list[str],
        default_admin_chat_id: int | None,
        bot_admin_chat_ids: list[int],
    ) -> None:
        if not tokens:
            return

        async with self._session_factory() as session:
            async with session.begin():
                existing_stmt = select(BotModel).where(BotModel.token.in_(tokens))
                existing_rows = (await session.execute(existing_stmt)).scalars().all()
                existing_by_token = {row.token: row for row in existing_rows}

                for index, token in enumerate(tokens):
                    admin_chat_id = (
                        bot_admin_chat_ids[index]
                        if index < len(bot_admin_chat_ids)
                        else default_admin_chat_id
                    )
                    if admin_chat_id is None:
                        raise ValueError(
                            "ADMIN_CHAT_ID is required when BOT_ADMIN_CHAT_IDS is incomplete."
                        )

                    bot_telegram_id, username = await self._resolve_bot_identity(token)
                    bot_record = existing_by_token.get(token)
                    if bot_record is None:
                        session.add(
                            BotModel(
                                token=token,
                                bot_telegram_id=bot_telegram_id,
                                username=username,
                                admin_chat_id=admin_chat_id,
                                is_active=True,
                            )
                        )
                    else:
                        bot_record.bot_telegram_id = bot_telegram_id
                        bot_record.username = username
                        bot_record.admin_chat_id = admin_chat_id
                        bot_record.is_active = True

                deactivate_stmt = select(BotModel).where(not_(BotModel.token.in_(tokens)))
                for row in (await session.execute(deactivate_stmt)).scalars().all():
                    row.is_active = False

    async def get_active_bots(self) -> list[BotRuntime]:
        async with self._session_factory() as session:
            stmt = select(BotModel).where(BotModel.is_active.is_(True))
            rows = (await session.execute(stmt)).scalars().all()
            return [
                BotRuntime(
                    db_bot_id=row.id,
                    token=row.token,
                    username=row.username,
                    admin_chat_id=row.admin_chat_id,
                )
                for row in rows
            ]

    async def _resolve_bot_identity(self, token: str) -> tuple[int, str | None]:
        temp_bot = Bot(token=token)
        try:
            me = await temp_bot.get_me()
            return me.id, me.username
        finally:
            await temp_bot.session.close()
            logger.info("Resolved bot identity for token ending with ...%s", token[-5:])
