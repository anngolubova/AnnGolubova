from __future__ import annotations

import asyncio
import contextlib
import logging

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from bot.factory import create_constructor_dispatcher, create_dispatcher
from bot.runtime import BotRuntime, ServiceContainer
from database.migrations import run_sqlite_compat_migrations
from database.session import create_engine_and_session_factory, init_database
from services.bot_registry_service import BotRegistryService
from services.polling_manager import ManagedBotsPollingManager
from utils.config import Settings
from utils.logging import setup_logging
from utils.process_lock import ProcessAlreadyRunningError, SingleInstanceLock

logger = logging.getLogger(__name__)


async def run_feedback_bot(runtime: BotRuntime, services: ServiceContainer, redis_url: str) -> None:
    bot = Bot(
        token=runtime.token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dispatcher = create_dispatcher(services, redis_url=redis_url)

    logger.info(
        "Starting polling for bot username=@%s admin_chat_id=%s",
        runtime.username,
        runtime.admin_chat_id,
    )
    try:
        await dispatcher.start_polling(
            bot,
            allowed_updates=dispatcher.resolve_used_update_types(),
        )
    except asyncio.CancelledError:
        logger.info("Managed bot polling cancelled for id=%s", runtime.db_bot_id)
        raise
    finally:
        await dispatcher.storage.close()
        await bot.session.close()


async def run_constructor_bot(
    *,
    constructor_bot_token: str,
    redis_url: str,
    session_factory,
) -> None:
    bot = Bot(
        token=constructor_bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dispatcher = create_constructor_dispatcher(
        session_factory=session_factory,
        redis_url=redis_url,
    )

    me = await bot.get_me()
    logger.info("Starting constructor bot @%s id=%s", me.username, me.id)
    try:
        await dispatcher.start_polling(
            bot,
            allowed_updates=dispatcher.resolve_used_update_types(),
        )
    except asyncio.CancelledError:
        logger.info("Constructor bot polling cancelled.")
        raise
    finally:
        await dispatcher.storage.close()
        await bot.session.close()


async def main() -> None:
    settings = Settings.from_env()
    setup_logging(settings.log_level)
    instance_lock = SingleInstanceLock("/tmp/telegram_feedback_constructor.lock")
    instance_lock.acquire()
    logger.info("Single-instance lock acquired.")

    engine = None
    polling_manager: ManagedBotsPollingManager | None = None
    tasks: list[asyncio.Task[None]] = []
    try:
        engine, session_factory = create_engine_and_session_factory(settings.database_url)
        await init_database(engine)
        await run_sqlite_compat_migrations(engine)

        registry_service = BotRegistryService(session_factory)
        seed_tokens = settings.bot_tokens
        if settings.constructor_bot_token:
            seed_tokens = [token for token in settings.bot_tokens if token != settings.constructor_bot_token]

        await registry_service.sync_from_tokens(
            tokens=seed_tokens,
            default_admin_chat_id=settings.admin_chat_id,
            bot_admin_chat_ids=settings.bot_admin_chat_ids,
        )

        async def _run_managed_runtime(runtime: BotRuntime) -> None:
            await run_feedback_bot(
                runtime,
                ServiceContainer(session_factory=session_factory, runtime=runtime),
                settings.redis_url,
            )

        exclude_tokens: set[str] = set()
        if settings.constructor_bot_token:
            exclude_tokens.add(settings.constructor_bot_token)
        polling_manager = ManagedBotsPollingManager(
            registry=registry_service,
            runner=_run_managed_runtime,
            refresh_interval_seconds=settings.managed_bots_sync_interval_seconds,
            exclude_tokens=exclude_tokens,
        )
        manager_task = asyncio.create_task(polling_manager.run_forever(), name="managed-bots-manager")

        constructor_task: asyncio.Task[None] | None = None
        if settings.constructor_bot_token:
            constructor_task = asyncio.create_task(
                run_constructor_bot(
                    constructor_bot_token=settings.constructor_bot_token,
                    redis_url=settings.redis_url,
                    session_factory=session_factory,
                ),
                name="constructor-bot",
            )
        else:
            logger.warning(
                "CONSTRUCTOR_BOT_TOKEN not set: constructor cabinet is disabled. "
                "Only managed feedback bots from DB/.env are running."
            )

        tasks = [manager_task] + ([constructor_task] if constructor_task else [])
        await asyncio.gather(*tasks)
    finally:
        if polling_manager is not None:
            await polling_manager.stop()
        for task in tasks:
            if task is None or task.done():
                continue
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task
        if engine is not None:
            await engine.dispose()
        instance_lock.release()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except ProcessAlreadyRunningError as error:
        logger.error(str(error))
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped by user.")
