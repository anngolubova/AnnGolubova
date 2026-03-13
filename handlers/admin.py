from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

from bot.runtime import ServiceContainer
from keyboards.admin import get_admin_keyboard
from services.broadcast_service import BroadcastService
from services.dialog_service import DialogService
from services.routing_service import RoutingService
from services.stats_service import StatsService
from utils.constants import ADMIN_START_TEXT, SUPPORTED_CONTENT_TYPES

logger = logging.getLogger(__name__)


class BroadcastState(StatesGroup):
    waiting_content = State()


def get_admin_router(services: ServiceContainer) -> Router:
    router = Router(name=f"admin_router_{services.runtime.db_bot_id}")
    dialog_service = DialogService(services.session_factory, services.runtime.db_bot_id)
    routing_service = RoutingService()
    stats_service = StatsService(services.session_factory, services.runtime.db_bot_id)
    broadcast_service = BroadcastService(services.session_factory, services.runtime.db_bot_id)

    def is_admin_chat(message: Message) -> bool:
        return message.chat.id == services.runtime.admin_chat_id

    @router.message(Command("start"), is_admin_chat)
    async def admin_start_handler(message: Message) -> None:
        await message.answer(ADMIN_START_TEXT, reply_markup=get_admin_keyboard())

    @router.message(Command("stats"), is_admin_chat)
    async def admin_stats_handler(message: Message) -> None:
        stats = await stats_service.get_snapshot()
        await message.answer(
            "Статистика:\n"
            f"• Пользователей: {stats.users_count}\n"
            f"• Диалогов: {stats.dialogs_count}\n"
            f"• Сообщений всего: {stats.messages_count}\n"
            f"• Сообщений за 24ч: {stats.messages_last_24h}"
        )

    @router.message(Command("broadcast"), is_admin_chat)
    async def admin_broadcast_command(message: Message, state: FSMContext) -> None:
        text = (message.text or "").strip()
        command_payload = text.split(maxsplit=1)

        if message.reply_to_message is not None:
            result = await broadcast_service.broadcast_from_message(
                bot=message.bot,
                source_message=message.reply_to_message,
            )
            await message.answer(
                f"Рассылка завершена: {result.sent}/{result.total}, ошибок: {result.failed}."
            )
            return

        if len(command_payload) > 1 and command_payload[1].strip():
            result = await broadcast_service.broadcast_text(
                bot=message.bot,
                admin_chat_id=message.chat.id,
                text=command_payload[1].strip(),
            )
            await message.answer(
                f"Рассылка завершена: {result.sent}/{result.total}, ошибок: {result.failed}."
            )
            return

        await state.set_state(BroadcastState.waiting_content)
        await message.answer(
            "Отправьте сообщение для рассылки (или /cancel для отмены).\n"
            "Можно отправить текст или медиа."
        )

    @router.message(Command("cancel"), is_admin_chat, BroadcastState.waiting_content)
    async def cancel_broadcast(message: Message, state: FSMContext) -> None:
        await state.clear()
        await message.answer("Режим рассылки отменён.")

    @router.message(
        is_admin_chat,
        BroadcastState.waiting_content,
        F.content_type.in_(SUPPORTED_CONTENT_TYPES),
    )
    async def admin_broadcast_content(message: Message, state: FSMContext) -> None:
        result = await broadcast_service.broadcast_from_message(
            bot=message.bot,
            source_message=message,
        )
        await state.clear()
        await message.answer(f"Рассылка завершена: {result.sent}/{result.total}, ошибок: {result.failed}.")

    @router.message(
        is_admin_chat,
        F.reply_to_message,
        F.content_type.in_(SUPPORTED_CONTENT_TYPES),
    )
    async def admin_reply_handler(message: Message) -> None:
        if message.text and message.text.startswith("/"):
            return
        if message.reply_to_message is None:
            return

        dialog_target = await dialog_service.resolve_dialog_by_admin_message(
            admin_chat_id=services.runtime.admin_chat_id,
            admin_message_id=message.reply_to_message.message_id,
        )
        if dialog_target is None:
            return

        try:
            user_message_id = await routing_service.send_admin_reply_to_user(
                bot=message.bot,
                admin_reply_message=message,
                user_telegram_id=dialog_target.user_telegram_id,
            )
            await dialog_service.save_admin_to_user_message(
                dialog_id=dialog_target.dialog_id,
                content_type=str(message.content_type),
                source_chat_id=message.chat.id,
                source_message_id=message.message_id,
                target_chat_id=dialog_target.user_telegram_id,
                target_message_id=user_message_id,
            )
        except (TelegramForbiddenError, TelegramBadRequest):
            logger.exception("Failed to deliver admin reply for dialog_id=%s", dialog_target.dialog_id)
            await message.answer("Не удалось доставить сообщение пользователю.")

    return router
