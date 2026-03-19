from __future__ import annotations

import logging
from dataclasses import dataclass

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.types import InlineKeyboardMarkup, Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from database.models import Dialog, MessageDirection, MessageRecord, User

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class BroadcastResult:
    total: int
    sent: int
    failed: int


class BroadcastService:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession], bot_id: int):
        self._session_factory = session_factory
        self._bot_id = bot_id

    async def broadcast_text(
        self,
        *,
        bot: Bot,
        admin_chat_id: int,
        text: str,
        reply_markup: InlineKeyboardMarkup | None = None,
    ) -> BroadcastResult:
        recipients = await self._get_dialog_recipients()
        sent = 0
        failed = 0
        records: list[MessageRecord] = []

        for user_telegram_id, dialog_id in recipients.items():
            try:
                out_message = await bot.send_message(
                    chat_id=user_telegram_id,
                    text=text,
                    reply_markup=reply_markup,
                )
                sent += 1
                records.append(
                    MessageRecord(
                        bot_id=self._bot_id,
                        dialog_id=dialog_id,
                        direction=MessageDirection.BROADCAST,
                        content_type="text",
                        source_chat_id=admin_chat_id,
                        source_message_id=0,
                        target_chat_id=user_telegram_id,
                        target_message_id=out_message.message_id,
                    )
                )
            except (TelegramForbiddenError, TelegramBadRequest):
                failed += 1
                logger.warning("Failed to broadcast text to user_id=%s", user_telegram_id)

        await self._persist_records(records)
        return BroadcastResult(total=len(recipients), sent=sent, failed=failed)

    async def broadcast_from_message(
        self,
        *,
        bot: Bot,
        source_message: Message,
        reply_markup: InlineKeyboardMarkup | None = None,
    ) -> BroadcastResult:
        recipients = await self._get_dialog_recipients()
        sent = 0
        failed = 0
        records: list[MessageRecord] = []

        for user_telegram_id, dialog_id in recipients.items():
            try:
                copied = await bot.copy_message(
                    chat_id=user_telegram_id,
                    from_chat_id=source_message.chat.id,
                    message_id=source_message.message_id,
                    reply_markup=reply_markup,
                )
                sent += 1
                records.append(
                    MessageRecord(
                        bot_id=self._bot_id,
                        dialog_id=dialog_id,
                        direction=MessageDirection.BROADCAST,
                        content_type=str(source_message.content_type),
                        source_chat_id=source_message.chat.id,
                        source_message_id=source_message.message_id,
                        target_chat_id=user_telegram_id,
                        target_message_id=copied.message_id,
                    )
                )
            except (TelegramForbiddenError, TelegramBadRequest):
                failed += 1
                logger.warning("Failed to copy broadcast to user_id=%s", user_telegram_id)

        await self._persist_records(records)
        return BroadcastResult(total=len(recipients), sent=sent, failed=failed)

    async def _get_dialog_recipients(self) -> dict[int, int]:
        async with self._session_factory() as session:
            stmt = (
                select(User.telegram_id, Dialog.id)
                .join(Dialog, Dialog.user_id == User.id)
                .where(Dialog.bot_id == self._bot_id)
            )
            rows = (await session.execute(stmt)).all()
            return {telegram_id: dialog_id for telegram_id, dialog_id in rows}

    async def _persist_records(self, records: list[MessageRecord]) -> None:
        if not records:
            return
        async with self._session_factory() as session:
            async with session.begin():
                session.add_all(records)
