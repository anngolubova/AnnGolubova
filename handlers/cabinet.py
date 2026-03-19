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
    BTN_HELP,
    BTN_FEEDBACK,
    BTN_LANG,
    BTN_MY_BOTS,
    BTN_MY_STATS,
    get_bot_details_keyboard,
    get_bots_inline_keyboard,
    get_cabinet_keyboard,
    get_cancel_keyboard,
    get_language_inline_keyboard,
)
from services.cabinet_service import CabinetService
from utils.constants import CONSTRUCTOR_FEEDBACK_TEXT, CONSTRUCTOR_HELP_TEXT, CONSTRUCTOR_WELCOME_TEMPLATE


class AddBotState(StatesGroup):
    waiting_token = State()
    waiting_title = State()


def get_cabinet_router(cabinet_service: CabinetService) -> Router:
    router = Router(name="constructor_cabinet_router")
    add_bot_aliases = {BTN_ADD_BOT, "Добавить бота"}
    my_bots_aliases = {BTN_MY_BOTS, "Мои боты"}
    my_stats_aliases = {BTN_MY_STATS, "Моя статистика"}
    export_aliases = {BTN_EXPORT_DB, "Выгрузка базы"}
    help_aliases = {BTN_HELP, "/help", "help", "Помощь"}
    feedback_aliases = {BTN_FEEDBACK, "/feedback", "feedback", "Связаться с нами"}
    lang_aliases = {BTN_LANG, "/lang", "lang", "Язык"}

    def _normalized_text(text: str | None) -> str:
        if not text:
            return ""
        # Normalize common mobile emoji variation selector.
        return text.replace("\uFE0F", "").strip()

    def _in_aliases(message: Message, aliases: set[str]) -> bool:
        return _normalized_text(message.text) in aliases

    def _normalize_lang(value: str | None) -> str:
        if not value:
            return "ru"
        candidate = value.strip().lower()
        if candidate.startswith("en"):
            return "en"
        return "ru"

    async def _admin_lang(user_id: int) -> str:
        return _normalize_lang(await cabinet_service.get_admin_language(user_id))

    def _welcome_text(lang: str, telegram_id: int) -> str:
        if lang == "en":
            return (
                "Feedback Bot Platform\n\n"
                f"Your Telegram ID: {telegram_id}\n\n"
                "How to connect a bot:\n"
                "1. Create a bot via @BotFather\n"
                "2. Copy API token\n"
                "3. Send token to this chat\n\n"
                "Commands:\n"
                "/help — full guide\n"
                "/cabinet — open cabinet\n"
                "/mybots — my bots\n"
                "/mystats — stats\n"
                "/feedback — contact us\n"
                "/lang — change language\n"
                "/bind — bind admin group\n"
                "/setwelcome — set client welcome\n"
                "/cancel — cancel action"
            )
        return CONSTRUCTOR_WELCOME_TEMPLATE.format(telegram_id=telegram_id)

    def _help_text(lang: str) -> str:
        if lang == "en":
            return (
                "How to create and connect a feedback bot\n\n"
                "Step 1 — Create a bot\n"
                "Open @BotFather, send /newbot, choose name and username.\n\n"
                "Step 2 — Copy token\n"
                "@BotFather will return token like:\n"
                "123456789:ABCdefGHI-jklMNOpqrsTUVwxyz_12345.\n\n"
                "Step 3 — Send token here\n"
                "Paste the token in this chat.\n"
                "System will validate and auto-start your bot.\n\n"
                "Step 4 — Create admin group\n"
                "Create Telegram group for support team.\n"
                "Add your bot to the group.\n"
                "Then send /bind in the group.\n\n"
                "Step 5 — Set welcome text\n"
                "Use /setwelcome to configure text clients see on first contact.\n\n"
                "Done! Clients write to your bot, messages appear in group.\n"
                "Reply there and client gets your response."
            )
        return CONSTRUCTOR_HELP_TEXT

    def _feedback_text(lang: str) -> str:
        if lang == "en":
            return (
                "Contact us:\n"
                "Describe your request in this chat and we will help you connect and configure your bot."
            )
        return CONSTRUCTOR_FEEDBACK_TEXT

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
        lang = await _admin_lang(message.from_user.id)
        await message.answer(
            _welcome_text(lang, message.from_user.id),
            reply_markup=get_cabinet_keyboard(),
        )

    @router.message(F.chat.type == ChatType.PRIVATE, Command("cabinet"))
    async def cabinet_open(message: Message) -> None:
        if message.from_user is not None:
            await cabinet_service.register_admin(message.from_user)
            lang = await _admin_lang(message.from_user.id)
            telegram_id = message.from_user.id
        else:
            lang = "ru"
            telegram_id = 0
        await message.answer(
            _welcome_text(lang, telegram_id),
            reply_markup=get_cabinet_keyboard(),
        )

    @router.message(F.chat.type == ChatType.PRIVATE, Command("help"))
    @router.message(F.chat.type == ChatType.PRIVATE, lambda message: _in_aliases(message, help_aliases))
    async def help_command(message: Message) -> None:
        if message.from_user is not None:
            await cabinet_service.register_admin(message.from_user)
            lang = await _admin_lang(message.from_user.id)
        else:
            lang = "ru"
        await message.answer(_help_text(lang), reply_markup=get_cabinet_keyboard())

    @router.message(F.chat.type == ChatType.PRIVATE, Command("feedback"))
    @router.message(F.chat.type == ChatType.PRIVATE, lambda message: _in_aliases(message, feedback_aliases))
    async def feedback_command(message: Message) -> None:
        if message.from_user is not None:
            await cabinet_service.register_admin(message.from_user)
            lang = await _admin_lang(message.from_user.id)
        else:
            lang = "ru"
        await message.answer(_feedback_text(lang), reply_markup=get_cabinet_keyboard())

    @router.message(F.chat.type == ChatType.PRIVATE, Command("lang"))
    @router.message(F.chat.type == ChatType.PRIVATE, lambda message: _in_aliases(message, lang_aliases))
    async def lang_command(message: Message) -> None:
        if message.from_user is not None:
            await cabinet_service.register_admin(message.from_user)
            lang = await _admin_lang(message.from_user.id)
        else:
            lang = "ru"
        prompt = "Выберите язык интерфейса:" if lang == "ru" else "Choose interface language:"
        await message.answer(prompt, reply_markup=get_language_inline_keyboard())

    @router.callback_query(F.data.startswith("cabinet:lang:"))
    async def callback_set_lang(callback: CallbackQuery) -> None:
        if callback.from_user is None:
            await callback.answer()
            return
        value = callback.data.split(":")[-1].strip().lower() if callback.data else "ru"
        selected = "en" if value == "en" else "ru"
        await cabinet_service.set_admin_language(callback.from_user.id, selected)
        if callback.message is not None:
            confirmation = (
                "Язык обновлён. Откройте /cabinet." if selected == "ru" else "Language updated. Open /cabinet."
            )
            await callback.message.answer(confirmation, reply_markup=get_cabinet_keyboard())
        await callback.answer("Готово" if selected == "ru" else "Done")

    @router.message(F.chat.type == ChatType.PRIVATE, Command("bind"))
    async def bind_hint_in_constructor(message: Message) -> None:
        await message.answer(
            "Команда /bind выполняется внутри группы администраторов, "
            "где уже добавлен ваш подключенный бот.\n\n"
            "Шаги:\n"
            "1) Добавьте подключенный бот в группу\n"
            "2) Отправьте /bind в этой группе\n"
            "3) Бот подтвердит привязку группы"
        )

    @router.message(F.chat.type == ChatType.PRIVATE, Command("setwelcome"))
    async def setwelcome_hint_in_constructor(message: Message) -> None:
        await message.answer(
            "Команда /setwelcome выполняется в админ-чате подключенного бота.\n\n"
            "Пример:\n"
            "/setwelcome Добро пожаловать! Опишите ваш вопрос, и мы скоро ответим."
        )

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
        lang = "ru"
        if message.from_user is not None:
            lang = await _admin_lang(message.from_user.id)
        await message.answer(
            (
                "Выберите действие через кнопки меню или используйте /help."
                if lang == "ru"
                else "Choose an action via menu buttons or use /help."
            ),
            reply_markup=get_cabinet_keyboard(),
        )

    return router
