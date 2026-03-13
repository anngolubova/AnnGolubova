from __future__ import annotations

from aiogram import Dispatcher
from aiogram.fsm.storage.redis import RedisStorage
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from bot.runtime import ServiceContainer
from handlers.admin import get_admin_router
from handlers.cabinet import get_cabinet_router
from handlers.errors import setup_error_handlers
from handlers.user import get_user_router
from services.bot_registry_service import BotRegistryService
from services.cabinet_service import CabinetService


def create_dispatcher(services: ServiceContainer, redis_url: str) -> Dispatcher:
    storage = RedisStorage.from_url(redis_url)
    dispatcher = Dispatcher(storage=storage)

    dispatcher.include_router(get_admin_router(services))
    dispatcher.include_router(get_user_router(services))
    setup_error_handlers(dispatcher)

    return dispatcher


def create_constructor_dispatcher(
    *,
    session_factory: async_sessionmaker[AsyncSession],
    redis_url: str,
) -> Dispatcher:
    storage = RedisStorage.from_url(redis_url)
    dispatcher = Dispatcher(storage=storage)

    registry = BotRegistryService(session_factory)
    cabinet_service = CabinetService(session_factory, registry)
    dispatcher.include_router(get_cabinet_router(cabinet_service))
    setup_error_handlers(dispatcher)

    return dispatcher
