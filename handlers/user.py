from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.enums import ChatType
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import CommandStart
from aiogram.types import Message

from bot.runtime import ServiceContainer
from services.dialog_service import DialogService
from services.routing_service import RoutingService
from utils.constants import SUPPORTED_CONTENT_TYPES, UNSUPPORTED_CONTENT_TEXT, USER_WELCOME_TEXT

logger = logging.getLogger(__name__)


def get_user_router(services: ServiceContainer) -> Router:
    router = Router(name=f"user_router_{services.runtime.db_bot_id}")
    dialog_service = DialogService(services.session_factory, services.runtime.db_bot_id)
    routing_service = RoutingService()

    @router.message(F.chat.type == ChatType.PRIVATE, CommandStart())
    async def start_handler(message: Message) -> None:
        if message.from_user is None:
            return
        await dialog_service.get_or_create_dialog_context(message.from_user)
        await message.answer(USER_WELCOME_TEXT)

    @router.message(
        F.chat.type == ChatType.PRIVATE,
        F.content_type.in_(SUPPORTED_CONTENT_TYPES),
    )
    async def user_message_handler(message: Message) -> None:
        if message.from_user is None:
            return

        dialog_context = await dialog_service.get_or_create_dialog_context(message.from_user)
        set_thread_root = dialog_context.thread_root_admin_message_id is None

        try:
            admin_message_id = await routing_service.forward_user_message_to_admin(
                bot=message.bot,
                incoming_message=message,
                admin_chat_id=services.runtime.admin_chat_id,
                thread_root_admin_message_id=dialog_context.thread_root_admin_message_id,
            )
            await dialog_service.save_user_to_admin_message(
                dialog_id=dialog_context.dialog_id,
                content_type=str(message.content_type),
                source_chat_id=message.chat.id,
                source_message_id=message.message_id,
                target_chat_id=services.runtime.admin_chat_id,
                target_message_id=admin_message_id,
                set_thread_root=set_thread_root,
            )
        except TelegramBadRequest:
            logger.exception("Failed to forward user message user_id=%s", message.from_user.id)
            await message.answer("Не удалось отправить сообщение. Попробуйте позже.")
            return

        if dialog_context.is_new_dialog:
            await message.answer("Ваше обращение отправлено. Ожидайте ответ администратора.")

    @router.message(F.chat.type == ChatType.PRIVATE)
    async def unsupported_handler(message: Message) -> None:
        await message.answer(UNSUPPORTED_CONTENT_TEXT)

    return router
