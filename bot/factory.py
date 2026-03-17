from __future__ import annotations

import logging

from aiogram import Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.redis import RedisStorage
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

logger = logging.getLogger(__name__)

from bot.runtime import ServiceContainer
from handlers.admin import get_admin_router
from handlers.cabinet import get_cabinet_router
from handlers.errors import setup_error_handlers
from handlers.user import get_user_router
from services.bot_registry_service import BotRegistryService
from services.cabinet_service import CabinetService


async def create_fsm_storage(redis_url: str):
    redis = Redis.from_url(redis_url)
    try:
        await redis.ping()
    except Exception:
        logger.warning(
            "Redis is unavailable at %s. Falling back to in-memory FSM storage.",
            redis_url,
        )
        await redis.aclose()
        return MemoryStorage()
    return RedisStorage(redis=redis)


def create_dispatcher(services: ServiceContainer, redis_url: str) -> Dispatcher:
    raise RuntimeError("Use create_dispatcher_async() instead of create_dispatcher().")


async def create_dispatcher_async(services: ServiceContainer, redis_url: str) -> Dispatcher:
    storage = await create_fsm_storage(redis_url)
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
    raise RuntimeError(
        "Use create_constructor_dispatcher_async() instead of create_constructor_dispatcher()."
    )


async def create_constructor_dispatcher_async(
    *,
    session_factory: async_sessionmaker[AsyncSession],
    redis_url: str,
) -> Dispatcher:
    storage = await create_fsm_storage(redis_url)
    dispatcher = Dispatcher(storage=storage)

    registry = BotRegistryService(session_factory)
    cabinet_service = CabinetService(session_factory, registry)
    dispatcher.include_router(get_cabinet_router(cabinet_service))
    setup_error_handlers(dispatcher)

    return dispatcher
