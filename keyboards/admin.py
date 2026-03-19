from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def get_admin_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="/stats"), KeyboardButton(text="/broadcast")],
            [KeyboardButton(text="/setwelcome"), KeyboardButton(text="/bind")],
            [KeyboardButton(text="/answer")],
            [KeyboardButton(text="/block"), KeyboardButton(text="/unblock")],
        ],
        resize_keyboard=True,
    )
