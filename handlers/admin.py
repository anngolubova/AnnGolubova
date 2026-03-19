from __future__ import annotations

import logging
from dataclasses import dataclass
from urllib.parse import urlparse

from aiogram import F, Router
from aiogram.enums import ChatType
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from bot.runtime import ServiceContainer
from keyboards.admin import get_admin_keyboard
from services.bot_registry_service import BotRegistryService
from services.broadcast_service import BroadcastService
from services.dialog_service import DialogService
from services.routing_service import RoutingService
from services.stats_service import StatsService
from utils.constants import ADMIN_START_TEXT, SUPPORTED_CONTENT_TYPES

logger = logging.getLogger(__name__)


class WelcomeState(StatesGroup):
    waiting_text = State()


@dataclass(slots=True)
class BroadcastDraft:
    text: str | None = None
    source_message: Message | None = None


def get_admin_router(services: ServiceContainer) -> Router:
    router = Router(name=f"admin_router_{services.runtime.db_bot_id}")
    dialog_service = DialogService(services.session_factory, services.runtime.db_bot_id)
    routing_service = RoutingService()
    stats_service = StatsService(services.session_factory, services.runtime.db_bot_id)
    broadcast_service = BroadcastService(services.session_factory, services.runtime.db_bot_id)
    registry_service = BotRegistryService(services.session_factory)

    def is_admin_chat(message: Message) -> bool:
        return message.chat.id == services.runtime.admin_chat_id

    pending_broadcast_content: set[tuple[int, int]] = set()
    pending_broadcast_buttons: set[tuple[int, int]] = set()
    broadcast_drafts: dict[tuple[int, int], BroadcastDraft] = {}

    def _admin_key(message: Message) -> tuple[int, int] | None:
        if message.from_user is None:
            return None
        return (message.chat.id, message.from_user.id)

    def _is_supported_broadcast_content(message: Message) -> bool:
        return message.content_type in SUPPORTED_CONTENT_TYPES

    def _awaiting_broadcast_content(message: Message) -> bool:
        key = _admin_key(message)
        return key in pending_broadcast_content if key is not None else False

    def _awaiting_broadcast_buttons(message: Message) -> bool:
        key = _admin_key(message)
        return key in pending_broadcast_buttons if key is not None else False

    def _clear_broadcast_flow(key: tuple[int, int]) -> None:
        pending_broadcast_content.discard(key)
        pending_broadcast_buttons.discard(key)
        broadcast_drafts.pop(key, None)

    def _build_buttons_help_text() -> str:
        return (
            "Добавьте кнопки (или /skip без кнопок).\n"
            "Формат: Текст - https://example.com\n"
            "Несколько кнопок в одной строке: Кнопка 1 - https://a.com | Кнопка 2 - https://b.com"
        )

    def _is_valid_button_url(url: str) -> bool:
        parsed = urlparse(url)
        if parsed.scheme in {"http", "https"}:
            return bool(parsed.netloc)
        if parsed.scheme == "tg":
            return bool(parsed.netloc or parsed.path)
        return False

    def _parse_button_line(item: str) -> tuple[str, str]:
        for separator in (" - ", " — "):
            if separator in item:
                title, url = item.split(separator, maxsplit=1)
                break
        else:
            raise ValueError(
                "Не удалось разобрать кнопки.\n"
                "Используйте формат: Текст - https://example.com"
            )

        title = title.strip()
        url = url.strip()
        if not title:
            raise ValueError("У кнопки отсутствует название.")
        if not _is_valid_button_url(url):
            raise ValueError(
                "Некорректная ссылка у кнопки.\n"
                "Разрешены URL с http://, https:// или tg://"
            )
        return title, url

    def _parse_inline_keyboard(raw: str) -> InlineKeyboardMarkup:
        rows: list[list[InlineKeyboardButton]] = []
        lines = [line.strip() for line in raw.splitlines() if line.strip()]
        if not lines:
            raise ValueError(
                "Пустой список кнопок.\n"
                "Используйте формат: Текст - https://example.com\n"
                "или отправьте /skip."
            )

        for line in lines:
            row: list[InlineKeyboardButton] = []
            parts = [part.strip() for part in line.split("|") if part.strip()]
            if not parts:
                continue
            for part in parts:
                title, url = _parse_button_line(part)
                row.append(InlineKeyboardButton(text=title, url=url))
            rows.append(row)

        if not rows:
            raise ValueError("Не найдено валидных кнопок. Отправьте /skip для рассылки без кнопок.")
        return InlineKeyboardMarkup(inline_keyboard=rows)

    @router.message(Command("start"), is_admin_chat)
    async def admin_start_handler(message: Message) -> None:
        await message.answer(ADMIN_START_TEXT, reply_markup=get_admin_keyboard())

    @router.message(Command("bind"), F.chat.type == ChatType.PRIVATE)
    async def bind_private_hint(message: Message) -> None:
        await message.answer(
            "Команда /bind выполняется в группе администраторов.\n"
            "Добавьте бота в группу и отправьте там /bind."
        )

    @router.message(Command("bind"), F.chat.type.in_({ChatType.GROUP, ChatType.SUPERGROUP}))
    async def bind_group_handler(message: Message) -> None:
        try:
            await registry_service.bind_admin_chat_for_runtime(
                db_bot_id=services.runtime.db_bot_id,
                actor_telegram_id=message.from_user.id if message.from_user else None,
                owner_admin_telegram_id=services.runtime.owner_admin_telegram_id,
                new_admin_chat_id=message.chat.id,
            )
        except ValueError as error:
            await message.answer(str(error))
            return

        services.runtime.admin_chat_id = message.chat.id
        await message.answer(
            "Группа успешно привязана как чат администраторов.\n"
            "Теперь ответы из этой группы будут уходить пользователям."
        )

    @router.message(Command("setwelcome"), is_admin_chat)
    async def set_welcome_command(message: Message, state: FSMContext) -> None:
        payload = (message.text or "").split(maxsplit=1)
        if len(payload) > 1 and payload[1].strip():
            try:
                welcome_text = await registry_service.set_welcome_text_for_runtime(
                    db_bot_id=services.runtime.db_bot_id,
                    actor_telegram_id=message.from_user.id if message.from_user else None,
                    owner_admin_telegram_id=services.runtime.owner_admin_telegram_id,
                    welcome_text=payload[1].strip(),
                )
            except ValueError as error:
                await message.answer(str(error))
                return

            services.runtime.welcome_text = welcome_text
            await state.clear()
            await message.answer("Приветствие обновлено.")
            return

        await state.set_state(WelcomeState.waiting_text)
        await message.answer(
            "Отправьте новый текст приветствия для клиентов.\n"
            "Для отмены используйте /cancel."
        )

    @router.message(is_admin_chat, WelcomeState.waiting_text, F.text)
    async def set_welcome_text_step(message: Message, state: FSMContext) -> None:
        try:
            welcome_text = await registry_service.set_welcome_text_for_runtime(
                db_bot_id=services.runtime.db_bot_id,
                actor_telegram_id=message.from_user.id if message.from_user else None,
                owner_admin_telegram_id=services.runtime.owner_admin_telegram_id,
                welcome_text=(message.text or "").strip(),
            )
        except ValueError as error:
            await message.answer(str(error))
            return

        services.runtime.welcome_text = welcome_text
        await state.clear()
        await message.answer("Приветствие сохранено.")

    @router.message(is_admin_chat, WelcomeState.waiting_text)
    async def set_welcome_non_text(message: Message) -> None:
        await message.answer("Отправьте текст приветствия или /cancel.")

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

    @router.message(Command("answer"), is_admin_chat)
    async def admin_answer_command(message: Message) -> None:
        text = (message.text or "").strip()
        parts = text.split(maxsplit=2)
        if len(parts) < 3:
            await message.answer("Формат: /answer <dialog_id> <текст>")
            return

        try:
            dialog_id = int(parts[1])
        except ValueError:
            await message.answer("dialog_id должен быть числом. Пример: /answer 15 Спасибо за сообщение!")
            return

        payload = parts[2].strip()
        if not payload:
            await message.answer("Текст ответа не должен быть пустым.")
            return

        target = await dialog_service.resolve_dialog_by_id(dialog_id=dialog_id)
        if target is None:
            await message.answer("Диалог не найден.")
            return

        try:
            out_message = await message.bot.send_message(chat_id=target.user_telegram_id, text=payload)
            await dialog_service.save_admin_to_user_message(
                dialog_id=target.dialog_id,
                content_type="text",
                source_chat_id=message.chat.id,
                source_message_id=message.message_id,
                target_chat_id=target.user_telegram_id,
                target_message_id=out_message.message_id,
            )
            await message.answer(f"Ответ отправлен в диалог #{dialog_id}.")
        except (TelegramForbiddenError, TelegramBadRequest):
            logger.exception("Failed /answer delivery for dialog_id=%s", dialog_id)
            await message.answer("Не удалось отправить сообщение пользователю.")

    @router.message(Command("block"), is_admin_chat)
    async def admin_block_command(message: Message) -> None:
        await _change_block_state(message, block=True)

    @router.message(Command("unblock"), is_admin_chat)
    async def admin_unblock_command(message: Message) -> None:
        await _change_block_state(message, block=False)

    async def _change_block_state(message: Message, *, block: bool) -> None:
        dialog_id: int | None = None
        if message.reply_to_message is not None:
            target = await dialog_service.resolve_dialog_by_admin_message(
                admin_chat_id=services.runtime.admin_chat_id,
                admin_message_id=message.reply_to_message.message_id,
            )
            if target is not None:
                dialog_id = target.dialog_id
        else:
            parts = (message.text or "").split(maxsplit=1)
            if len(parts) > 1:
                try:
                    dialog_id = int(parts[1].strip())
                except ValueError:
                    dialog_id = None

        if dialog_id is None:
            await message.answer(
                "Формат:\n"
                f"• /{'block' if block else 'unblock'} <dialog_id>\n"
                "или отправьте команду реплаем на сообщение пользователя."
            )
            return

        changed = await dialog_service.set_user_block_status_by_dialog_id(
            dialog_id=dialog_id,
            blocked=block,
        )
        if not changed:
            await message.answer("Диалог не найден.")
            return
        await message.answer(
            f"Пользователь диалога #{dialog_id} {'заблокирован' if block else 'разблокирован'}."
        )

    @router.message(Command("broadcast"), is_admin_chat)
    async def admin_broadcast_command(message: Message, state: FSMContext) -> None:
        key = _admin_key(message)
        if key is None:
            await message.answer("Не удалось определить администратора. Повторите команду от обычного аккаунта.")
            return

        await state.clear()
        _clear_broadcast_flow(key)

        text = (message.text or "").strip()
        command_payload = text.split(maxsplit=1)

        if message.reply_to_message is not None:
            if not _is_supported_broadcast_content(message.reply_to_message):
                await message.answer(
                    "Этот тип контента пока нельзя отправить в рассылку.\n"
                    "Разрешено: текст, голос, фото, видео, аудио, документ."
                )
                return

            broadcast_drafts[key] = BroadcastDraft(source_message=message.reply_to_message)
            pending_broadcast_buttons.add(key)
            await message.answer(
                "Контент для рассылки принят из реплая.\n"
                f"{_build_buttons_help_text()}"
            )
            return

        if len(command_payload) > 1 and command_payload[1].strip():
            broadcast_drafts[key] = BroadcastDraft(text=command_payload[1].strip())
            pending_broadcast_buttons.add(key)
            await message.answer(
                "Текст для рассылки принят.\n"
                f"{_build_buttons_help_text()}"
            )
            return

        pending_broadcast_content.add(key)
        await message.answer(
            "Отправьте сообщение для рассылки (или /cancel для отмены).\n"
            "Можно отправить текст или медиа, затем при необходимости добавить кнопки."
        )

    @router.message(Command("cancel"), is_admin_chat)
    async def cancel_broadcast(message: Message, state: FSMContext) -> None:
        key = _admin_key(message)
        if key is not None:
            _clear_broadcast_flow(key)
        await state.clear()
        await message.answer("Текущее действие отменено.")

    @router.message(
        is_admin_chat,
        _awaiting_broadcast_content,
        F.content_type.in_(SUPPORTED_CONTENT_TYPES),
    )
    async def admin_broadcast_content(message: Message) -> None:
        key = _admin_key(message)
        if key is None:
            await message.answer("Не удалось определить администратора. Повторите /broadcast.")
            return

        pending_broadcast_content.discard(key)
        if message.content_type == "text":
            broadcast_drafts[key] = BroadcastDraft(text=message.text or "")
        else:
            broadcast_drafts[key] = BroadcastDraft(source_message=message)
        pending_broadcast_buttons.add(key)
        await message.answer(
            "Контент принят.\n"
            f"{_build_buttons_help_text()}"
        )

    @router.message(
        is_admin_chat,
        _awaiting_broadcast_content,
    )
    async def admin_broadcast_content_unsupported(message: Message) -> None:
        await message.answer(
            "Неподдерживаемый тип контента для рассылки.\n"
            "Разрешено: текст, голос, фото, видео, аудио, документ."
        )

    @router.message(
        is_admin_chat,
        _awaiting_broadcast_buttons,
        F.text,
    )
    async def admin_broadcast_buttons_step(message: Message) -> None:
        key = _admin_key(message)
        if key is None:
            await message.answer("Не удалось определить администратора. Повторите /broadcast.")
            return

        raw_text = (message.text or "").strip()
        if not raw_text:
            await message.answer("Отправьте кнопки текстом или /skip.")
            return
        if raw_text.lower() == "/skip":
            reply_markup = None
        else:
            if raw_text.startswith("/"):
                await message.answer(
                    "Для отправки без кнопок используйте /skip,\n"
                    "для отмены — /cancel."
                )
                return
            try:
                reply_markup = _parse_inline_keyboard(raw_text)
            except ValueError as error:
                await message.answer(str(error))
                return

        draft = broadcast_drafts.get(key)
        if draft is None:
            _clear_broadcast_flow(key)
            await message.answer("Черновик рассылки не найден. Повторите /broadcast.")
            return

        if draft.source_message is not None:
            result = await broadcast_service.broadcast_from_message(
                bot=message.bot,
                source_message=draft.source_message,
                reply_markup=reply_markup,
            )
        elif draft.text is not None:
            result = await broadcast_service.broadcast_text(
                bot=message.bot,
                admin_chat_id=message.chat.id,
                text=draft.text,
                reply_markup=reply_markup,
            )
        else:
            _clear_broadcast_flow(key)
            await message.answer("Пустой черновик рассылки. Повторите /broadcast.")
            return

        _clear_broadcast_flow(key)
        await message.answer(f"Рассылка завершена: {result.sent}/{result.total}, ошибок: {result.failed}.")

    @router.message(
        is_admin_chat,
        _awaiting_broadcast_buttons,
    )
    async def admin_broadcast_buttons_non_text(message: Message) -> None:
        await message.answer("Отправьте кнопки текстом или /skip.")

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

    @router.message(is_admin_chat, F.chat.type == ChatType.PRIVATE)
    async def admin_private_fallback(message: Message) -> None:
        if message.reply_to_message is not None:
            await message.answer(
                "Для ответа пользователю используйте только: текст, голос, фото, видео, аудио, документ."
            )
            return

        await message.answer(
            "Панель администратора:\n"
            "• Ответ пользователю: реплай на пересланное сообщение\n"
            "• Ответ без реплая: /answer <dialog_id> <текст>\n"
            "• /block <dialog_id> — блокировка пользователя\n"
            "• /unblock <dialog_id> — снять блокировку\n"
            "• /stats — статистика\n"
            "• /broadcast — рассылка (с возможностью кнопок)\n"
            "• /bind — привязать группу\n"
            "• /setwelcome — приветствие клиентов"
        )

    return router
