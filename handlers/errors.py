from __future__ import annotations

import logging

from aiogram import Dispatcher
from aiogram.types.error_event import ErrorEvent

logger = logging.getLogger(__name__)


def setup_error_handlers(dispatcher: Dispatcher) -> None:
    async def _global_error_handler(event: ErrorEvent) -> bool:
        logger.exception("Unhandled exception while processing update", exc_info=event.exception)
        return True

    dispatcher.errors.register(_global_error_handler)
