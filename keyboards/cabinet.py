from __future__ import annotations

from collections.abc import Sequence

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from services.cabinet_service import AdminBotCard

BTN_ADD_BOT = "➕ Добавить бота"
BTN_MY_BOTS = "🤖 Мои боты"
BTN_MY_STATS = "📊 Моя статистика"
BTN_EXPORT_DB = "📥 Выгрузка базы"
BTN_HELP = "ℹ️ /help"
BTN_CANCEL = "❌ Отмена"


def get_cabinet_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_ADD_BOT), KeyboardButton(text=BTN_MY_BOTS)],
            [KeyboardButton(text=BTN_MY_STATS), KeyboardButton(text=BTN_EXPORT_DB)],
            [KeyboardButton(text=BTN_HELP)],
        ],
        resize_keyboard=True,
    )


def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=BTN_CANCEL)]],
        resize_keyboard=True,
    )


def get_bots_inline_keyboard(cards: Sequence[AdminBotCard]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for card in cards:
        status = "🟢" if card.runtime.is_active else "🔴"
        title = card.runtime.title or card.runtime.username or f"bot_{card.runtime.db_bot_id}"
        builder.row(
            InlineKeyboardButton(
                text=f"{status} {title}",
                callback_data=f"cabinet:view:{card.runtime.db_bot_id}",
            ),
            InlineKeyboardButton(
                text="Вкл/Выкл",
                callback_data=f"cabinet:toggle:{card.runtime.db_bot_id}",
            ),
        )
    return builder.as_markup()


def get_bot_details_keyboard(db_bot_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔄 Переключить статус",
                    callback_data=f"cabinet:toggle:{db_bot_id}",
                ),
                InlineKeyboardButton(
                    text="↩️ Назад к списку",
                    callback_data="cabinet:list",
                ),
            ]
        ]
    )
