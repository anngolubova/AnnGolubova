from __future__ import annotations

from collections.abc import Sequence

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from services.cabinet_service import AdminBotCard

BTN_ADD_BOT = "➕ Добавить бота"
BTN_ADD_BOT_EN = "➕ Add bot"
BTN_MY_BOTS = "🤖 Мои боты"
BTN_MY_BOTS_EN = "🤖 My bots"
BTN_MY_STATS = "📊 Моя статистика"
BTN_MY_STATS_EN = "📊 My stats"
BTN_EXPORT_DB = "📥 Выгрузка базы"
BTN_EXPORT_DB_EN = "📥 Export database"
BTN_HELP = "ℹ️ /help"
BTN_FEEDBACK = "💬 /feedback"
BTN_LANG = "🌐 /lang"
BTN_CANCEL = "❌ Отмена"
BTN_CANCEL_EN = "❌ Cancel"

TOGGLE_BUTTON_TEXT = "Вкл/Выкл"
TOGGLE_BUTTON_TEXT_EN = "On/Off"
TOGGLE_STATUS_TEXT = "🔄 Переключить статус"
TOGGLE_STATUS_TEXT_EN = "🔄 Toggle status"
BACK_LIST_TEXT = "↩️ Назад к списку"
BACK_LIST_TEXT_EN = "↩️ Back to list"
WELCOME_BUTTON_TEXT = "✏️ Приветствие"
WELCOME_BUTTON_TEXT_EN = "✏️ Welcome text"

def _normalize_lang(lang: str | None) -> str:
    if not lang:
        return "ru"
    return "en" if lang.lower().startswith("en") else "ru"


def get_cabinet_keyboard(lang: str = "ru") -> ReplyKeyboardMarkup:
    normalized = _normalize_lang(lang)
    add_bot = BTN_ADD_BOT if normalized == "ru" else BTN_ADD_BOT_EN
    my_bots = BTN_MY_BOTS if normalized == "ru" else BTN_MY_BOTS_EN
    my_stats = BTN_MY_STATS if normalized == "ru" else BTN_MY_STATS_EN
    export_db = BTN_EXPORT_DB if normalized == "ru" else BTN_EXPORT_DB_EN
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=add_bot), KeyboardButton(text=my_bots)],
            [KeyboardButton(text=my_stats), KeyboardButton(text=export_db)],
            [KeyboardButton(text=BTN_HELP), KeyboardButton(text=BTN_FEEDBACK)],
            [KeyboardButton(text=BTN_LANG)],
        ],
        resize_keyboard=True,
    )


def get_cancel_keyboard(lang: str = "ru") -> ReplyKeyboardMarkup:
    cancel_text = BTN_CANCEL if _normalize_lang(lang) == "ru" else BTN_CANCEL_EN
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=cancel_text)]],
        resize_keyboard=True,
    )


def get_bots_inline_keyboard(cards: Sequence[AdminBotCard], lang: str = "ru") -> InlineKeyboardMarkup:
    normalized = _normalize_lang(lang)
    toggle_text = TOGGLE_BUTTON_TEXT if normalized == "ru" else TOGGLE_BUTTON_TEXT_EN
    details_prefix = "Подробнее" if normalized == "ru" else "Details"
    builder = InlineKeyboardBuilder()
    for card in cards:
        status = "🟢" if card.runtime.is_active else "🔴"
        title = card.runtime.title or card.runtime.username or f"bot_{card.runtime.db_bot_id}"
        builder.row(
            InlineKeyboardButton(
                text=f"{details_prefix}: {status} {title}",
                callback_data=f"cabinet:view:{card.runtime.db_bot_id}",
            ),
            InlineKeyboardButton(
                text=toggle_text,
                callback_data=f"cabinet:toggle:{card.runtime.db_bot_id}",
            ),
        )
    return builder.as_markup()


def get_bot_details_keyboard(db_bot_id: int, lang: str = "ru") -> InlineKeyboardMarkup:
    normalized = _normalize_lang(lang)
    toggle_status = TOGGLE_STATUS_TEXT if normalized == "ru" else TOGGLE_STATUS_TEXT_EN
    back_list = BACK_LIST_TEXT if normalized == "ru" else BACK_LIST_TEXT_EN
    welcome_text = WELCOME_BUTTON_TEXT if normalized == "ru" else WELCOME_BUTTON_TEXT_EN
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=welcome_text,
                    callback_data=f"cabinet:setwelcome:{db_bot_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=toggle_status,
                    callback_data=f"cabinet:toggle:{db_bot_id}",
                ),
                InlineKeyboardButton(
                    text=back_list,
                    callback_data="cabinet:list",
                ),
            ]
        ]
    )


def get_language_inline_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    normalized = _normalize_lang(lang)
    ru_label = "✅ Русский" if normalized == "ru" else "Русский"
    en_label = "English" if normalized == "ru" else "✅ English"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=ru_label, callback_data="cabinet:lang:ru"),
                InlineKeyboardButton(text=en_label, callback_data="cabinet:lang:en"),
            ]
        ]
    )
