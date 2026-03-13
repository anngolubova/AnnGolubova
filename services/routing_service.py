from __future__ import annotations

import logging

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import Message

logger = logging.getLogger(__name__)


class RoutingService:
    async def forward_user_message_to_admin(
        self,
        *,
        bot: Bot,
        incoming_message: Message,
        admin_chat_id: int,
        thread_root_admin_message_id: int | None,
    ) -> int:
        reply_to_id = thread_root_admin_message_id

        try:
            copied = await bot.copy_message(
                chat_id=admin_chat_id,
                from_chat_id=incoming_message.chat.id,
                message_id=incoming_message.message_id,
                reply_to_message_id=reply_to_id,
            )
            return copied.message_id
        except TelegramBadRequest:
            logger.warning(
                "Failed to reply to thread root. Forwarding without reply_to. "
                "admin_chat_id=%s root_message_id=%s",
                admin_chat_id,
                reply_to_id,
            )
            copied = await bot.copy_message(
                chat_id=admin_chat_id,
                from_chat_id=incoming_message.chat.id,
                message_id=incoming_message.message_id,
            )
            return copied.message_id

    async def send_admin_reply_to_user(
        self,
        *,
        bot: Bot,
        admin_reply_message: Message,
        user_telegram_id: int,
    ) -> int:
        copied = await bot.copy_message(
            chat_id=user_telegram_id,
            from_chat_id=admin_reply_message.chat.id,
            message_id=admin_reply_message.message_id,
        )
        return copied.message_id
