from aiogram.enums import ContentType

SUPPORTED_CONTENT_TYPES: set[ContentType] = {
    ContentType.TEXT,
    ContentType.VOICE,
    ContentType.PHOTO,
    ContentType.VIDEO,
    ContentType.AUDIO,
    ContentType.DOCUMENT,
}

USER_WELCOME_TEXT = (
    "Здравствуйте! Это анонимная форма обратной связи.\n\n"
    "Отправьте текст, голос, фото, видео, аудио или документ — "
    "сообщение будет передано администратору."
)

UNSUPPORTED_CONTENT_TEXT = (
    "Этот тип контента пока не поддерживается.\n"
    "Доступно: текст, голос, фото, видео, аудио, документ."
)

ADMIN_START_TEXT = (
    "Панель администратора активна.\n"
    "• Отвечайте реплаем на пересланные сообщения пользователей.\n"
    "• /stats — статистика\n"
    "• /broadcast — режим рассылки"
)
