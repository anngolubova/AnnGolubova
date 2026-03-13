from __future__ import annotations

from aiogram import Dispatcher
from aiogram.fsm.storage.redis import RedisStorage

from bot.runtime import ServiceContainer
from handlers.admin import get_admin_router
from handlers.errors import setup_error_handlers
from handlers.user import get_user_router


def create_dispatcher(services: ServiceContainer, redis_url: str) -> Dispatcher:
    storage = RedisStorage.from_url(redis_url)
    dispatcher = Dispatcher(storage=storage)

    dispatcher.include_router(get_admin_router(services))
    dispatcher.include_router(get_user_router(services))
    setup_error_handlers(dispatcher)

    return dispatcher
