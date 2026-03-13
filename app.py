from __future__ import annotations

import asyncio
import logging

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from bot.factory import create_dispatcher
from bot.runtime import BotRuntime, ServiceContainer
from database.session import create_engine_and_session_factory, init_database
from services.bot_registry_service import BotRegistryService
from utils.config import Settings
from utils.logging import setup_logging

logger = logging.getLogger(__name__)


async def run_bot(runtime: BotRuntime, services: ServiceContainer, redis_url: str) -> None:
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
    finally:
        await dispatcher.storage.close()
        await bot.session.close()


async def main() -> None:
    settings = Settings.from_env()
    setup_logging(settings.log_level)

    engine, session_factory = create_engine_and_session_factory(settings.database_url)
    await init_database(engine)

    registry_service = BotRegistryService(session_factory)
    await registry_service.sync_from_tokens(
        tokens=settings.bot_tokens,
        default_admin_chat_id=settings.admin_chat_id,
        bot_admin_chat_ids=settings.bot_admin_chat_ids,
    )
    runtimes = await registry_service.get_active_bots()
    if not runtimes:
        raise RuntimeError("No active bots were configured.")

    try:
        await asyncio.gather(
            *[
                run_bot(
                    runtime,
                    ServiceContainer(session_factory=session_factory, runtime=runtime),
                    settings.redis_url,
                )
                for runtime in runtimes
            ]
        )
    finally:
        await engine.dispose()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped by user.")
