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
    BTN_ADD_BOT_EN,
    BTN_CANCEL,
    BTN_CANCEL_EN,
    BTN_EXPORT_DB,
    BTN_EXPORT_DB_EN,
    BTN_FEEDBACK,
    BTN_HELP,
    BTN_LANG,
    BTN_MY_BOTS,
    BTN_MY_BOTS_EN,
    BTN_MY_STATS,
    BTN_MY_STATS_EN,
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


class ServiceBroadcastState(StatesGroup):
    waiting_text = State()


class BotWelcomeState(StatesGroup):
    waiting_text = State()


def get_cabinet_router(cabinet_service: CabinetService) -> Router:
    router = Router(name="constructor_cabinet_router")

    MESSAGES: dict[str, dict[str, str]] = {
        "bind_hint": {
            "ru": (
                "Команда /bind выполняется внутри группы администраторов, "
                "где уже добавлен ваш подключенный бот.\n\n"
                "Шаги:\n"
                "1) Добавьте подключенный бот в группу\n"
                "2) Отправьте /bind в этой группе\n"
                "3) Бот подтвердит привязку группы"
            ),
            "en": (
                "The /bind command must be used in the admin group where your connected bot is already added.\n\n"
                "Steps:\n"
                "1) Add the connected bot to your group\n"
                "2) Send /bind in that group\n"
                "3) Bot confirms group binding"
            ),
        },
        "setwelcome_hint": {
            "ru": (
                "Изменение приветствия доступно в кабинете.\n\n"
                "Варианты:\n"
                "1) /mybots → Подробнее → ✏️ Приветствие\n"
                "2) /setwelcome <bot_id> <текст>\n"
                "3) /setwelcome <bot_id> - (сброс к стандартному)"
            ),
            "en": (
                "Welcome text update is available in cabinet.\n\n"
                "Options:\n"
                "1) /mybots → Details → ✏️ Welcome text\n"
                "2) /setwelcome <bot_id> <text>\n"
                "3) /setwelcome <bot_id> - (reset to default)"
            ),
        },
        "mybots_empty": {
            "ru": "У вас пока нет подключённых ботов. Нажмите 'Добавить бота'.",
            "en": "You do not have connected bots yet. Tap 'Add bot'.",
        },
        "mybots_title": {"ru": "Ваши боты:", "en": "Your bots:"},
        "bots_list_empty": {"ru": "Список ботов пуст.", "en": "Bot list is empty."},
        "dashboard_title": {"ru": "Ваш кабинет:", "en": "Your cabinet:"},
        "dashboard_lines": {
            "ru": (
                "• Ботов: {bots_total}\n"
                "• Активных ботов: {bots_active}\n"
                "• Пользователей: {users_total}\n"
                "• Диалогов: {dialogs_total}\n"
                "• Сообщений: {messages_total}"
            ),
            "en": (
                "• Bots: {bots_total}\n"
                "• Active bots: {bots_active}\n"
                "• Users: {users_total}\n"
                "• Dialogs: {dialogs_total}\n"
                "• Messages: {messages_total}"
            ),
        },
        "cancelled": {"ru": "Действие отменено.", "en": "Action cancelled."},
        "ask_token": {
            "ru": "Отправьте токен нового бота из @BotFather.",
            "en": "Send a new bot token from @BotFather.",
        },
        "token_bad_format": {
            "ru": "Неверный формат токена. Попробуйте снова.",
            "en": "Invalid token format. Please try again.",
        },
        "ask_title": {
            "ru": "Введите название для кабинета (или отправьте '-' чтобы пропустить).",
            "en": "Enter bot title for cabinet (or send '-' to skip).",
        },
        "session_reset": {
            "ru": "Сессия добавления бота сброшена. Нажмите 'Добавить бота' снова.",
            "en": "Bot adding session was reset. Tap 'Add bot' again.",
        },
        "add_failed": {
            "ru": "Не удалось добавить бота: {error}\nНажмите 'Добавить бота' и попробуйте снова.",
            "en": "Failed to add bot: {error}\nTap 'Add bot' and try again.",
        },
        "add_success": {
            "ru": (
                "Бот {bot_label} успешно подключён.\n"
                "Теперь он запустится автоматически и будет пересылать обращения в ваш чат."
            ),
            "en": (
                "Bot {bot_label} was connected successfully.\n"
                "It will start automatically and forward user messages to your admin chat."
            ),
        },
        "bad_callback": {"ru": "Некорректные данные кнопки.", "en": "Invalid button payload."},
        "bot_not_found": {"ru": "Бот не найден", "en": "Bot not found"},
        "status_active": {"ru": "активен", "en": "active"},
        "status_inactive": {"ru": "остановлен", "en": "stopped"},
        "bot_details": {
            "ru": (
                "Бот: {title}\n"
                "Статус: {status}\n"
                "Пользователей: {users_total}\n"
                "Диалогов: {dialogs_total}\n"
                "Сообщений: {messages_total}"
            ),
            "en": (
                "Bot: {title}\n"
                "Status: {status}\n"
                "Users: {users_total}\n"
                "Dialogs: {dialogs_total}\n"
                "Messages: {messages_total}"
            ),
        },
        "toggle_done": {"ru": "Бот {state_text}.", "en": "Bot is {state_text}."},
        "toggle_state_on": {"ru": "включен", "en": "enabled"},
        "toggle_state_off": {"ru": "выключен", "en": "disabled"},
        "lang_prompt": {"ru": "Выберите язык интерфейса:", "en": "Choose interface language:"},
        "lang_updated": {
            "ru": "Язык обновлён. Откройте /cabinet.",
            "en": "Language updated. Open /cabinet.",
        },
        "done": {"ru": "Готово", "en": "Done"},
        "export_empty": {"ru": "Нет данных для выгрузки.", "en": "No data available for export."},
        "export_caption": {
            "ru": "Выгрузка базы пользователей готова.",
            "en": "User database export is ready.",
        },
        "service_broadcast_forbidden": {
            "ru": "Команда доступна только владельцу сервиса.",
            "en": "This command is available only for the service owner.",
        },
        "service_broadcast_prompt": {
            "ru": (
                "Отправьте текст глобальной рассылки для всех экземпляров.\n"
                "Для отмены используйте /cancel."
            ),
            "en": (
                "Send text for global broadcast across all instances.\n"
                "Use /cancel to abort."
            ),
        },
        "service_broadcast_done": {
            "ru": (
                "Глобальная рассылка завершена.\n"
                "• Экземпляров всего: {bots_total}\n"
                "• Экземпляров успешно: {bots_sent}\n"
                "• Экземпляров с ошибками: {bots_failed}\n"
                "• Получателей всего: {users_total}\n"
                "• Доставлено: {sent}\n"
                "• Ошибок доставки: {failed}"
            ),
            "en": (
                "Global broadcast completed.\n"
                "• Instances total: {bots_total}\n"
                "• Instances succeeded: {bots_sent}\n"
                "• Instances failed: {bots_failed}\n"
                "• Recipients total: {users_total}\n"
                "• Delivered: {sent}\n"
                "• Delivery failures: {failed}"
            ),
        },
        "setwelcome_no_bots": {
            "ru": "У вас нет подключённых ботов. Сначала добавьте бота.",
            "en": "You do not have connected bots yet. Add a bot first.",
        },
        "setwelcome_format": {
            "ru": "Формат: /setwelcome <bot_id> <текст> (или '-' для сброса)",
            "en": "Format: /setwelcome <bot_id> <text> (or '-' to reset)",
        },
        "setwelcome_select_prompt": {
            "ru": "Выберите бота в списке и нажмите «✏️ Приветствие».",
            "en": "Select a bot in the list and tap “✏️ Welcome text”.",
        },
        "setwelcome_enter_text": {
            "ru": (
                "Отправьте новый текст приветствия для этого бота.\n"
                "Отправьте '-' чтобы вернуть стандартное приветствие.\n"
                "Для отмены используйте /cancel."
            ),
            "en": (
                "Send new welcome text for this bot.\n"
                "Send '-' to restore default welcome text.\n"
                "Use /cancel to abort."
            ),
        },
        "setwelcome_updated": {
            "ru": "Приветствие обновлено.",
            "en": "Welcome text was updated.",
        },
        "setwelcome_reset": {
            "ru": "Приветствие сброшено на стандартное.",
            "en": "Welcome text was reset to default.",
        },
        "setwelcome_state_lost": {
            "ru": "Сессия изменения приветствия устарела. Повторите через /mybots.",
            "en": "Welcome edit session expired. Repeat via /mybots.",
        },
        "unknown": {
            "ru": "Выберите действие через кнопки меню или используйте /help.",
            "en": "Choose an action via menu buttons or use /help.",
        },
    }

    add_bot_aliases = {BTN_ADD_BOT, BTN_ADD_BOT_EN, "Добавить бота", "Add bot"}
    my_bots_aliases = {BTN_MY_BOTS, BTN_MY_BOTS_EN, "Мои боты", "My bots"}
    my_stats_aliases = {BTN_MY_STATS, BTN_MY_STATS_EN, "Моя статистика", "My stats"}
    export_aliases = {BTN_EXPORT_DB, BTN_EXPORT_DB_EN, "Выгрузка базы", "Export database"}
    help_aliases = {BTN_HELP, "/help", "help", "Помощь", "Help"}
    feedback_aliases = {BTN_FEEDBACK, "/feedback", "feedback", "Связаться с нами", "Contact us"}
    lang_aliases = {BTN_LANG, "/lang", "lang", "Язык", "Language"}
    cancel_aliases = {BTN_CANCEL, BTN_CANCEL_EN}

    def _normalized_text(text: str | None) -> str:
        if not text:
            return ""
        return text.replace("\uFE0F", "").strip()

    def _normalize_lang(value: str | None) -> str:
        if not value:
            return "ru"
        candidate = value.strip().lower()
        if candidate.startswith("en"):
            return "en"
        return "ru"

    def _t(lang: str, key: str, **kwargs) -> str:
        value = MESSAGES[key]["en" if lang == "en" else "ru"]
        return value.format(**kwargs) if kwargs else value

    def _in_aliases(message: Message, aliases: set[str]) -> bool:
        return _normalized_text(message.text) in aliases

    async def _admin_lang(user_id: int) -> str:
        try:
            return _normalize_lang(await cabinet_service.get_admin_language(user_id))
        except Exception:
            return "ru"

    async def _ensure_admin_and_lang(message: Message) -> str:
        if message.from_user is None:
            return "ru"
        await cabinet_service.register_admin(message.from_user)
        return await _admin_lang(message.from_user.id)

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
            if "message is not modified" not in str(error).lower():
                raise

    async def _apply_welcome_text(
        *,
        message: Message,
        lang: str,
        db_bot_id: int,
        raw_text: str,
    ) -> bool:
        normalized = raw_text.strip()
        if not normalized:
            await message.answer(_t(lang, "setwelcome_format"), reply_markup=get_cancel_keyboard(lang))
            return False
        if message.from_user is None:
            return False

        new_welcome = None if normalized == "-" else normalized
        try:
            stored = await cabinet_service.set_bot_welcome_text(
                admin_telegram_id=message.from_user.id,
                db_bot_id=db_bot_id,
                welcome_text=new_welcome,
            )
        except ValueError as error:
            await message.answer(str(error), reply_markup=get_cabinet_keyboard(lang))
            return False

        text = _t(lang, "setwelcome_reset") if stored is None else _t(lang, "setwelcome_updated")
        await message.answer(text, reply_markup=get_cabinet_keyboard(lang))
        return True

    @router.message(F.chat.type == ChatType.PRIVATE, Command("start"))
    async def cabinet_start(message: Message) -> None:
        if message.from_user is None:
            return
        lang = await _ensure_admin_and_lang(message)
        await message.answer(
            _welcome_text(lang, message.from_user.id),
            reply_markup=get_cabinet_keyboard(lang),
        )

    @router.message(F.chat.type == ChatType.PRIVATE, Command("cabinet"))
    async def cabinet_open(message: Message) -> None:
        lang = await _ensure_admin_and_lang(message)
        telegram_id = message.from_user.id if message.from_user else 0
        await message.answer(
            _welcome_text(lang, telegram_id),
            reply_markup=get_cabinet_keyboard(lang),
        )

    @router.message(F.chat.type == ChatType.PRIVATE, Command("help"))
    @router.message(F.chat.type == ChatType.PRIVATE, lambda message: _in_aliases(message, help_aliases))
    async def help_command(message: Message) -> None:
        lang = await _ensure_admin_and_lang(message)
        await message.answer(_help_text(lang), reply_markup=get_cabinet_keyboard(lang))

    @router.message(F.chat.type == ChatType.PRIVATE, Command("feedback"))
    @router.message(F.chat.type == ChatType.PRIVATE, lambda message: _in_aliases(message, feedback_aliases))
    async def feedback_command(message: Message) -> None:
        lang = await _ensure_admin_and_lang(message)
        await message.answer(_feedback_text(lang), reply_markup=get_cabinet_keyboard(lang))

    @router.message(F.chat.type == ChatType.PRIVATE, Command("lang"))
    @router.message(F.chat.type == ChatType.PRIVATE, lambda message: _in_aliases(message, lang_aliases))
    async def lang_command(message: Message) -> None:
        lang = await _ensure_admin_and_lang(message)
        await message.answer(_t(lang, "lang_prompt"), reply_markup=get_language_inline_keyboard(lang))

    @router.callback_query(F.data.startswith("cabinet:lang:"))
    async def callback_set_lang(callback: CallbackQuery) -> None:
        if callback.from_user is None:
            await callback.answer()
            return
        value = callback.data.split(":")[-1].strip().lower() if callback.data else "ru"
        selected = "en" if value == "en" else "ru"
        await cabinet_service.set_admin_language(callback.from_user.id, selected)
        if callback.message is not None:
            await callback.message.answer(
                _t(selected, "lang_updated"),
                reply_markup=get_cabinet_keyboard(selected),
            )
        await callback.answer(_t(selected, "done"))

    @router.message(F.chat.type == ChatType.PRIVATE, Command("bind"))
    async def bind_hint_in_constructor(message: Message) -> None:
        lang = await _ensure_admin_and_lang(message)
        await message.answer(_t(lang, "bind_hint"), reply_markup=get_cabinet_keyboard(lang))

    @router.message(F.chat.type == ChatType.PRIVATE, Command("setwelcome"))
    async def setwelcome_hint_in_constructor(message: Message) -> None:
        if message.from_user is None:
            return
        lang = await _ensure_admin_and_lang(message)
        payload = (message.text or "").split(maxsplit=2)
        if len(payload) >= 3:
            try:
                db_bot_id = int(payload[1])
            except ValueError:
                await message.answer(_t(lang, "setwelcome_format"), reply_markup=get_cabinet_keyboard(lang))
                return
            await _apply_welcome_text(
                message=message,
                lang=lang,
                db_bot_id=db_bot_id,
                raw_text=payload[2],
            )
            return

        cards = await cabinet_service.list_admin_bots_with_stats(message.from_user.id)
        if not cards:
            await message.answer(_t(lang, "setwelcome_no_bots"), reply_markup=get_cabinet_keyboard(lang))
            return
        await message.answer(
            f"{_t(lang, 'setwelcome_hint')}\n\n{_t(lang, 'setwelcome_select_prompt')}",
            reply_markup=get_bots_inline_keyboard(cards, lang),
        )

    @router.message(F.chat.type == ChatType.PRIVATE, Command("mybots"))
    async def my_bots_command(message: Message) -> None:
        if message.from_user is None:
            return
        lang = await _ensure_admin_and_lang(message)
        cards = await cabinet_service.list_admin_bots_with_stats(message.from_user.id)
        if not cards:
            await message.answer(_t(lang, "mybots_empty"), reply_markup=get_cabinet_keyboard(lang))
            return
        await message.answer(_t(lang, "mybots_title"), reply_markup=get_bots_inline_keyboard(cards, lang))

    @router.message(F.chat.type == ChatType.PRIVATE, Command("mystats"))
    async def my_stats_command(message: Message) -> None:
        if message.from_user is None:
            return
        lang = await _ensure_admin_and_lang(message)
        snapshot = await cabinet_service.get_dashboard(message.from_user.id)
        await message.answer(
            f"{_t(lang, 'dashboard_title')}\n"
            f"{_t(lang, 'dashboard_lines', bots_total=snapshot.bots_total, bots_active=snapshot.bots_active, users_total=snapshot.users_total, dialogs_total=snapshot.dialogs_total, messages_total=snapshot.messages_total)}",
            reply_markup=get_cabinet_keyboard(lang),
        )

    @router.message(F.chat.type == ChatType.PRIVATE, Command("service_broadcast"))
    async def service_broadcast_command(message: Message, state: FSMContext) -> None:
        if message.from_user is None:
            return
        lang = await _ensure_admin_and_lang(message)
        if not cabinet_service.is_service_owner(message.from_user.id):
            await message.answer(
                _t(lang, "service_broadcast_forbidden"),
                reply_markup=get_cabinet_keyboard(lang),
            )
            return

        payload = (message.text or "").split(maxsplit=1)
        if len(payload) > 1 and payload[1].strip():
            try:
                summary = await cabinet_service.service_broadcast_text(
                    owner_telegram_id=message.from_user.id,
                    text=payload[1].strip(),
                )
            except ValueError as error:
                await message.answer(str(error), reply_markup=get_cabinet_keyboard(lang))
                return
            await message.answer(
                _t(
                    lang,
                    "service_broadcast_done",
                    bots_total=summary.bots_total,
                    bots_sent=summary.bots_sent,
                    bots_failed=summary.bots_failed,
                    users_total=summary.users_total,
                    sent=summary.sent,
                    failed=summary.failed,
                ),
                reply_markup=get_cabinet_keyboard(lang),
            )
            return

        await state.set_state(ServiceBroadcastState.waiting_text)
        await message.answer(_t(lang, "service_broadcast_prompt"), reply_markup=get_cancel_keyboard(lang))

    @router.message(F.chat.type == ChatType.PRIVATE, Command("cancel"))
    @router.message(F.chat.type == ChatType.PRIVATE, lambda message: _in_aliases(message, cancel_aliases))
    async def cancel_flow(message: Message, state: FSMContext) -> None:
        lang = await _ensure_admin_and_lang(message)
        await state.clear()
        await message.answer(_t(lang, "cancelled"), reply_markup=get_cabinet_keyboard(lang))

    @router.message(F.chat.type == ChatType.PRIVATE, ServiceBroadcastState.waiting_text, F.text)
    async def service_broadcast_text_step(message: Message, state: FSMContext) -> None:
        if message.from_user is None:
            return
        if (message.text or "").startswith("/"):
            return

        lang = await _ensure_admin_and_lang(message)
        if not cabinet_service.is_service_owner(message.from_user.id):
            await state.clear()
            await message.answer(
                _t(lang, "service_broadcast_forbidden"),
                reply_markup=get_cabinet_keyboard(lang),
            )
            return

        try:
            summary = await cabinet_service.service_broadcast_text(
                owner_telegram_id=message.from_user.id,
                text=message.text or "",
            )
        except ValueError as error:
            await message.answer(str(error), reply_markup=get_cancel_keyboard(lang))
            return

        await state.clear()
        await message.answer(
            _t(
                lang,
                "service_broadcast_done",
                bots_total=summary.bots_total,
                bots_sent=summary.bots_sent,
                bots_failed=summary.bots_failed,
                users_total=summary.users_total,
                sent=summary.sent,
                failed=summary.failed,
            ),
            reply_markup=get_cabinet_keyboard(lang),
        )

    @router.message(F.chat.type == ChatType.PRIVATE, lambda message: _in_aliases(message, add_bot_aliases))
    async def add_bot_clicked(message: Message, state: FSMContext) -> None:
        lang = await _ensure_admin_and_lang(message)
        await state.set_state(AddBotState.waiting_token)
        await message.answer(_t(lang, "ask_token"), reply_markup=get_cancel_keyboard(lang))

    @router.message(F.chat.type == ChatType.PRIVATE, AddBotState.waiting_token, F.text)
    async def add_bot_token_step(message: Message, state: FSMContext) -> None:
        lang = await _ensure_admin_and_lang(message)
        raw_token = (message.text or "").strip()
        if ":" not in raw_token:
            await message.answer(_t(lang, "token_bad_format"), reply_markup=get_cancel_keyboard(lang))
            return
        await state.update_data(token=raw_token)
        await state.set_state(AddBotState.waiting_title)
        await message.answer(_t(lang, "ask_title"), reply_markup=get_cancel_keyboard(lang))

    @router.message(F.chat.type == ChatType.PRIVATE, AddBotState.waiting_title, F.text)
    async def add_bot_title_step(message: Message, state: FSMContext) -> None:
        if message.from_user is None:
            return
        lang = await _ensure_admin_and_lang(message)
        data = await state.get_data()
        token = str(data.get("token", "")).strip()
        if not token:
            await state.clear()
            await message.answer(_t(lang, "session_reset"), reply_markup=get_cabinet_keyboard(lang))
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
                _t(lang, "add_failed", error=str(error)),
                reply_markup=get_cabinet_keyboard(lang),
            )
            return

        await state.clear()
        bot_label = runtime.title or runtime.username or f"id={runtime.db_bot_id}"
        await message.answer(
            _t(lang, "add_success", bot_label=bot_label),
            reply_markup=get_cabinet_keyboard(lang),
        )

    @router.message(F.chat.type == ChatType.PRIVATE, lambda message: _in_aliases(message, my_bots_aliases))
    async def show_my_bots(message: Message) -> None:
        if message.from_user is None:
            return
        lang = await _ensure_admin_and_lang(message)
        cards = await cabinet_service.list_admin_bots_with_stats(message.from_user.id)
        if not cards:
            await message.answer(_t(lang, "mybots_empty"), reply_markup=get_cabinet_keyboard(lang))
            return
        await message.answer(_t(lang, "mybots_title"), reply_markup=get_bots_inline_keyboard(cards, lang))

    @router.callback_query(F.data == "cabinet:list")
    async def callback_list_bots(callback: CallbackQuery) -> None:
        if callback.from_user is None:
            return
        lang = await _admin_lang(callback.from_user.id)
        cards = await cabinet_service.list_admin_bots_with_stats(callback.from_user.id)
        text = _t(lang, "mybots_title") if cards else _t(lang, "bots_list_empty")
        await _safe_edit_text(
            callback,
            text=text,
            reply_markup=get_bots_inline_keyboard(cards, lang) if cards else None,
        )
        await callback.answer()

    @router.callback_query(F.data.startswith("cabinet:view:"))
    async def callback_view_bot(callback: CallbackQuery) -> None:
        if callback.from_user is None:
            return
        if callback.message is None:
            await callback.answer()
            return

        lang = await _admin_lang(callback.from_user.id)
        try:
            db_bot_id = int(callback.data.split(":")[-1])
        except (TypeError, ValueError):
            await callback.answer(_t(lang, "bad_callback"), show_alert=True)
            return

        cards = await cabinet_service.list_admin_bots_with_stats(callback.from_user.id)
        card = next((item for item in cards if item.runtime.db_bot_id == db_bot_id), None)
        if card is None:
            await callback.answer(_t(lang, "bot_not_found"), show_alert=True)
            return

        status = _t(lang, "status_active") if card.runtime.is_active else _t(lang, "status_inactive")
        title = card.runtime.title or card.runtime.username or f"bot_{card.runtime.db_bot_id}"
        await _safe_edit_text(
            callback,
            text=_t(
                lang,
                "bot_details",
                title=title,
                status=status,
                users_total=card.users_total,
                dialogs_total=card.dialogs_total,
                messages_total=card.messages_total,
            ),
            reply_markup=get_bot_details_keyboard(card.runtime.db_bot_id, lang),
        )
        await callback.answer()

    @router.callback_query(F.data.startswith("cabinet:setwelcome:"))
    async def callback_set_welcome(callback: CallbackQuery, state: FSMContext) -> None:
        if callback.from_user is None:
            return
        lang = await _admin_lang(callback.from_user.id)
        try:
            db_bot_id = int(callback.data.split(":")[-1])
        except (TypeError, ValueError):
            await callback.answer(_t(lang, "bad_callback"), show_alert=True)
            return

        cards = await cabinet_service.list_admin_bots_with_stats(callback.from_user.id)
        card = next((item for item in cards if item.runtime.db_bot_id == db_bot_id), None)
        if card is None:
            await callback.answer(_t(lang, "bot_not_found"), show_alert=True)
            return

        await state.set_state(BotWelcomeState.waiting_text)
        await state.update_data(setwelcome_bot_id=db_bot_id)
        if callback.message is not None:
            await callback.message.answer(
                _t(lang, "setwelcome_enter_text"),
                reply_markup=get_cancel_keyboard(lang),
            )
        await callback.answer(_t(lang, "done"))

    @router.callback_query(F.data.startswith("cabinet:toggle:"))
    async def callback_toggle_bot(callback: CallbackQuery) -> None:
        if callback.from_user is None:
            return
        lang = await _admin_lang(callback.from_user.id)
        try:
            db_bot_id = int(callback.data.split(":")[-1])
        except (TypeError, ValueError):
            await callback.answer(_t(lang, "bad_callback"), show_alert=True)
            return

        try:
            is_active = await cabinet_service.toggle_bot(
                admin_telegram_id=callback.from_user.id,
                db_bot_id=db_bot_id,
            )
        except ValueError as error:
            await callback.answer(str(error), show_alert=True)
            return

        state_text = _t(lang, "toggle_state_on") if is_active else _t(lang, "toggle_state_off")
        await callback.answer(_t(lang, "toggle_done", state_text=state_text))

        cards = await cabinet_service.list_admin_bots_with_stats(callback.from_user.id)
        await _safe_edit_text(
            callback,
            text=_t(lang, "mybots_title"),
            reply_markup=get_bots_inline_keyboard(cards, lang) if cards else None,
        )

    @router.message(F.chat.type == ChatType.PRIVATE, BotWelcomeState.waiting_text, F.text)
    async def set_welcome_text_step(message: Message, state: FSMContext) -> None:
        if message.from_user is None:
            return
        if (message.text or "").startswith("/"):
            return

        lang = await _ensure_admin_and_lang(message)
        data = await state.get_data()
        try:
            db_bot_id = int(data.get("setwelcome_bot_id"))
        except (TypeError, ValueError):
            await state.clear()
            await message.answer(_t(lang, "setwelcome_state_lost"), reply_markup=get_cabinet_keyboard(lang))
            return

        is_done = await _apply_welcome_text(
            message=message,
            lang=lang,
            db_bot_id=db_bot_id,
            raw_text=message.text or "",
        )
        if is_done:
            await state.clear()

    @router.message(F.chat.type == ChatType.PRIVATE, BotWelcomeState.waiting_text)
    async def set_welcome_non_text(message: Message) -> None:
        lang = await _ensure_admin_and_lang(message)
        await message.answer(_t(lang, "setwelcome_enter_text"), reply_markup=get_cancel_keyboard(lang))

    @router.message(F.chat.type == ChatType.PRIVATE, lambda message: _in_aliases(message, my_stats_aliases))
    async def show_dashboard(message: Message) -> None:
        if message.from_user is None:
            return
        lang = await _ensure_admin_and_lang(message)
        snapshot = await cabinet_service.get_dashboard(message.from_user.id)
        await message.answer(
            f"{_t(lang, 'dashboard_title')}\n"
            f"{_t(lang, 'dashboard_lines', bots_total=snapshot.bots_total, bots_active=snapshot.bots_active, users_total=snapshot.users_total, dialogs_total=snapshot.dialogs_total, messages_total=snapshot.messages_total)}",
            reply_markup=get_cabinet_keyboard(lang),
        )

    @router.message(F.chat.type == ChatType.PRIVATE, lambda message: _in_aliases(message, export_aliases))
    async def export_database(message: Message) -> None:
        if message.from_user is None:
            return
        lang = await _ensure_admin_and_lang(message)
        filename, payload = await cabinet_service.export_users_csv(message.from_user.id)
        if not payload:
            await message.answer(_t(lang, "export_empty"), reply_markup=get_cabinet_keyboard(lang))
            return
        await message.answer_document(
            BufferedInputFile(payload, filename=filename),
            caption=_t(lang, "export_caption"),
        )

    @router.message(F.chat.type == ChatType.PRIVATE)
    async def unknown_private_input(message: Message, state: FSMContext) -> None:
        if await state.get_state() is not None:
            return
        lang = await _ensure_admin_and_lang(message)
        await message.answer(_t(lang, "unknown"), reply_markup=get_cabinet_keyboard(lang))

    return router
