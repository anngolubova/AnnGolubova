from __future__ import annotations

from aiogram import F, Router
from aiogram.enums import ChatType
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import BufferedInputFile, CallbackQuery, Message

from keyboards.cabinet import (
    BTN_ADD_BOT,
    BTN_CANCEL,
    BTN_EXPORT_DB,
    BTN_MY_BOTS,
    BTN_MY_STATS,
    get_bot_details_keyboard,
    get_bots_inline_keyboard,
    get_cabinet_keyboard,
    get_cancel_keyboard,
)
from services.cabinet_service import CabinetService


class AddBotState(StatesGroup):
    waiting_token = State()
    waiting_title = State()


def get_cabinet_router(cabinet_service: CabinetService) -> Router:
    router = Router(name="constructor_cabinet_router")
    add_bot_aliases = {BTN_ADD_BOT, "Добавить бота"}
    my_bots_aliases = {BTN_MY_BOTS, "Мои боты"}
    my_stats_aliases = {BTN_MY_STATS, "Моя статистика"}
    export_aliases = {BTN_EXPORT_DB, "Выгрузка базы"}

    def _normalized_text(text: str | None) -> str:
        if not text:
            return ""
        # Normalize common mobile emoji variation selector.
        return text.replace("\uFE0F", "").strip()

    def _in_aliases(message: Message, aliases: set[str]) -> bool:
        return _normalized_text(message.text) in aliases

    async def _safe_edit_text(callback: CallbackQuery, *, text: str, reply_markup=None) -> None:
        if callback.message is None:
            return
        try:
            await callback.message.edit_text(text, reply_markup=reply_markup)
        except TelegramBadRequest as error:
            # Avoid noisy crashes when text/markup has not changed.
            if "message is not modified" not in str(error).lower():
                raise

    @router.message(F.chat.type == ChatType.PRIVATE, Command("start"))
    async def cabinet_start(message: Message) -> None:
        if message.from_user is None:
            return
        await cabinet_service.register_admin(message.from_user)
        await message.answer(
            "Добро пожаловать в бот-конструктор.\n"
            "Здесь можно подключать свои боты, смотреть статистику и выгружать базу.",
            reply_markup=get_cabinet_keyboard(),
        )

    @router.message(F.chat.type == ChatType.PRIVATE, Command("cabinet"))
    async def cabinet_open(message: Message) -> None:
        if message.from_user is not None:
            await cabinet_service.register_admin(message.from_user)
        await message.answer("Личный кабинет открыт.", reply_markup=get_cabinet_keyboard())

    @router.message(F.chat.type == ChatType.PRIVATE, Command("mybots"))
    async def my_bots_command(message: Message) -> None:
        if message.from_user is None:
            return
        await cabinet_service.register_admin(message.from_user)
        cards = await cabinet_service.list_admin_bots_with_stats(message.from_user.id)
        if not cards:
            await message.answer("У вас пока нет подключённых ботов. Нажмите 'Добавить бота'.")
            return
        await message.answer("Ваши боты:", reply_markup=get_bots_inline_keyboard(cards))

    @router.message(F.chat.type == ChatType.PRIVATE, Command("mystats"))
    async def my_stats_command(message: Message) -> None:
        if message.from_user is None:
            return
        await cabinet_service.register_admin(message.from_user)
        snapshot = await cabinet_service.get_dashboard(message.from_user.id)
        await message.answer(
            "Ваш кабинет:\n"
            f"• Ботов: {snapshot.bots_total}\n"
            f"• Активных ботов: {snapshot.bots_active}\n"
            f"• Пользователей: {snapshot.users_total}\n"
            f"• Диалогов: {snapshot.dialogs_total}\n"
            f"• Сообщений: {snapshot.messages_total}"
        )

    @router.message(F.chat.type == ChatType.PRIVATE, Command("cancel"))
    @router.message(F.chat.type == ChatType.PRIVATE, F.text == BTN_CANCEL)
    async def cancel_flow(message: Message, state: FSMContext) -> None:
        await state.clear()
        await message.answer("Действие отменено.", reply_markup=get_cabinet_keyboard())

    @router.message(F.chat.type == ChatType.PRIVATE, lambda message: _in_aliases(message, add_bot_aliases))
    async def add_bot_clicked(message: Message, state: FSMContext) -> None:
        if message.from_user is not None:
            await cabinet_service.register_admin(message.from_user)
        await state.set_state(AddBotState.waiting_token)
        await message.answer(
            "Отправьте токен нового бота из @BotFather.",
            reply_markup=get_cancel_keyboard(),
        )

    @router.message(F.chat.type == ChatType.PRIVATE, AddBotState.waiting_token, F.text)
    async def add_bot_token_step(message: Message, state: FSMContext) -> None:
        raw_token = (message.text or "").strip()
        if ":" not in raw_token:
            await message.answer("Неверный формат токена. Попробуйте снова.")
            return
        await state.update_data(token=raw_token)
        await state.set_state(AddBotState.waiting_title)
        await message.answer(
            "Введите название для кабинета (или отправьте '-' чтобы пропустить).",
            reply_markup=get_cancel_keyboard(),
        )

    @router.message(F.chat.type == ChatType.PRIVATE, AddBotState.waiting_title, F.text)
    async def add_bot_title_step(message: Message, state: FSMContext) -> None:
        if message.from_user is None:
            return
        data = await state.get_data()
        token = str(data.get("token", "")).strip()
        if not token:
            await state.clear()
            await message.answer(
                "Сессия добавления бота сброшена. Нажмите 'Добавить бота' снова.",
                reply_markup=get_cabinet_keyboard(),
            )
            return

        title = (message.text or "").strip()
        if title == "-":
            title = None
        try:
            runtime = await cabinet_service.add_bot(
                admin_telegram_id=message.from_user.id,
                token=token,
                title=title,
            )
        except ValueError as error:
            await state.clear()
            await message.answer(
                f"Не удалось добавить бота: {error}\n"
                "Нажмите 'Добавить бота' и попробуйте снова.",
                reply_markup=get_cabinet_keyboard(),
            )
            return

        await state.clear()
        bot_label = runtime.title or runtime.username or f"id={runtime.db_bot_id}"
        await message.answer(
            f"Бот {bot_label} успешно подключён.\n"
            "Теперь он запустится автоматически и будет пересылать обращения в ваш чат.",
            reply_markup=get_cabinet_keyboard(),
        )

    @router.message(F.chat.type == ChatType.PRIVATE, lambda message: _in_aliases(message, my_bots_aliases))
    async def show_my_bots(message: Message) -> None:
        if message.from_user is None:
            return
        await cabinet_service.register_admin(message.from_user)
        cards = await cabinet_service.list_admin_bots_with_stats(message.from_user.id)
        if not cards:
            await message.answer("У вас пока нет подключённых ботов. Нажмите 'Добавить бота'.")
            return
        await message.answer(
            "Ваши боты:",
            reply_markup=get_bots_inline_keyboard(cards),
        )

    @router.callback_query(F.data == "cabinet:list")
    async def callback_list_bots(callback: CallbackQuery) -> None:
        if callback.from_user is None:
            return
        cards = await cabinet_service.list_admin_bots_with_stats(callback.from_user.id)
        text = "Ваши боты:" if cards else "Список ботов пуст."
        await _safe_edit_text(
            callback,
            text=text,
            reply_markup=get_bots_inline_keyboard(cards) if cards else None,
        )
        await callback.answer()

    @router.callback_query(F.data.startswith("cabinet:view:"))
    async def callback_view_bot(callback: CallbackQuery) -> None:
        if callback.from_user is None:
            return
        if callback.message is None:
            await callback.answer()
            return

        try:
            db_bot_id = int(callback.data.split(":")[-1])
        except (TypeError, ValueError):
            await callback.answer("Некорректные данные кнопки.", show_alert=True)
            return
        cards = await cabinet_service.list_admin_bots_with_stats(callback.from_user.id)
        card = next((item for item in cards if item.runtime.db_bot_id == db_bot_id), None)
        if card is None:
            await callback.answer("Бот не найден", show_alert=True)
            return

        status = "активен" if card.runtime.is_active else "остановлен"
        title = card.runtime.title or card.runtime.username or f"bot_{card.runtime.db_bot_id}"
        await _safe_edit_text(
            callback,
            text=(
                f"Бот: {title}\n"
                f"Статус: {status}\n"
                f"Пользователей: {card.users_total}\n"
                f"Диалогов: {card.dialogs_total}\n"
                f"Сообщений: {card.messages_total}"
            ),
            reply_markup=get_bot_details_keyboard(card.runtime.db_bot_id),
        )
        await callback.answer()

    @router.callback_query(F.data.startswith("cabinet:toggle:"))
    async def callback_toggle_bot(callback: CallbackQuery) -> None:
        if callback.from_user is None:
            return
        try:
            db_bot_id = int(callback.data.split(":")[-1])
        except (TypeError, ValueError):
            await callback.answer("Некорректные данные кнопки.", show_alert=True)
            return
        try:
            is_active = await cabinet_service.toggle_bot(
                admin_telegram_id=callback.from_user.id,
                db_bot_id=db_bot_id,
            )
        except ValueError as error:
            await callback.answer(str(error), show_alert=True)
            return

        state_text = "включен" if is_active else "выключен"
        await callback.answer(f"Бот {state_text}.")

        cards = await cabinet_service.list_admin_bots_with_stats(callback.from_user.id)
        await _safe_edit_text(
            callback,
            text="Ваши боты:",
            reply_markup=get_bots_inline_keyboard(cards) if cards else None,
        )

    @router.message(F.chat.type == ChatType.PRIVATE, lambda message: _in_aliases(message, my_stats_aliases))
    async def show_dashboard(message: Message) -> None:
        if message.from_user is None:
            return
        await cabinet_service.register_admin(message.from_user)
        snapshot = await cabinet_service.get_dashboard(message.from_user.id)
        await message.answer(
            "Ваш кабинет:\n"
            f"• Ботов: {snapshot.bots_total}\n"
            f"• Активных ботов: {snapshot.bots_active}\n"
            f"• Пользователей: {snapshot.users_total}\n"
            f"• Диалогов: {snapshot.dialogs_total}\n"
            f"• Сообщений: {snapshot.messages_total}"
        )

    @router.message(F.chat.type == ChatType.PRIVATE, lambda message: _in_aliases(message, export_aliases))
    async def export_database(message: Message) -> None:
        if message.from_user is None:
            return
        await cabinet_service.register_admin(message.from_user)
        filename, payload = await cabinet_service.export_users_csv(message.from_user.id)
        if not payload:
            await message.answer("Нет данных для выгрузки.")
            return
        await message.answer_document(
            BufferedInputFile(payload, filename=filename),
            caption="Выгрузка базы пользователей готова.",
        )

    @router.message(F.chat.type == ChatType.PRIVATE)
    async def unknown_private_input(message: Message, state: FSMContext) -> None:
        if await state.get_state() is not None:
            return
        await message.answer(
            "Выберите действие через кнопки меню или используйте /cabinet.",
            reply_markup=get_cabinet_keyboard(),
        )

    return router
