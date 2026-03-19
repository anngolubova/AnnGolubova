from __future__ import annotations

import csv
import logging
from dataclasses import dataclass
from io import BytesIO, StringIO

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError, TelegramUnauthorizedError
from aiogram.types import User as TelegramUser
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from bot.runtime import BotRuntime
from database.models import AdminAccount, BotModel, Dialog, MessageRecord, User
from services.bot_registry_service import BotRegistryService
from services.broadcast_service import BroadcastService

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class AdminDashboard:
    bots_total: int
    bots_active: int
    users_total: int
    dialogs_total: int
    messages_total: int


@dataclass(slots=True)
class AdminBotCard:
    runtime: BotRuntime
    users_total: int
    dialogs_total: int
    messages_total: int


@dataclass(slots=True)
class ServiceBroadcastSummary:
    bots_total: int
    bots_sent: int
    bots_failed: int
    users_total: int
    sent: int
    failed: int


class CabinetService:
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        registry: BotRegistryService,
        *,
        service_owner_telegram_ids: set[int] | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._registry = registry
        self._service_owner_telegram_ids = service_owner_telegram_ids or set()

    async def register_admin(self, tg_admin: TelegramUser) -> None:
        await self._registry.upsert_admin(
            telegram_id=tg_admin.id,
            username=tg_admin.username,
            first_name=tg_admin.first_name,
            last_name=tg_admin.last_name,
            telegram_language_code=tg_admin.language_code,
        )

    async def get_admin_language(self, admin_telegram_id: int) -> str:
        return await self._registry.get_admin_ui_language(admin_telegram_id)

    async def set_admin_language(self, admin_telegram_id: int, language: str) -> str:
        return await self._registry.set_admin_ui_language(admin_telegram_id, language)

    async def add_bot(self, *, admin_telegram_id: int, token: str, title: str | None) -> BotRuntime:
        return await self._registry.add_bot_for_admin(
            admin_telegram_id=admin_telegram_id,
            token=token.strip(),
            title=title.strip() if title else None,
        )

    def is_service_owner(self, admin_telegram_id: int) -> bool:
        return admin_telegram_id in self._service_owner_telegram_ids

    async def service_broadcast_text(
        self,
        *,
        owner_telegram_id: int,
        text: str,
    ) -> ServiceBroadcastSummary:
        if not self.is_service_owner(owner_telegram_id):
            raise ValueError("Команда доступна только владельцу сервиса.")

        payload = text.strip()
        if not payload:
            raise ValueError("Текст глобальной рассылки не должен быть пустым.")

        runtimes = await self._registry.get_all_bots()
        summary = ServiceBroadcastSummary(
            bots_total=len(runtimes),
            bots_sent=0,
            bots_failed=0,
            users_total=0,
            sent=0,
            failed=0,
        )
        for runtime in runtimes:
            bot = Bot(token=runtime.token)
            try:
                broadcast_service = BroadcastService(self._session_factory, runtime.db_bot_id)
                result = await broadcast_service.broadcast_text(
                    bot=bot,
                    admin_chat_id=owner_telegram_id,
                    text=payload,
                )
                summary.bots_sent += 1
                summary.users_total += result.total
                summary.sent += result.sent
                summary.failed += result.failed
            except (TelegramUnauthorizedError, TelegramForbiddenError, TelegramBadRequest, Exception):
                summary.bots_failed += 1
                logger.exception(
                    "Service broadcast failed for bot runtime id=%s username=@%s",
                    runtime.db_bot_id,
                    runtime.username,
                )
            finally:
                await bot.session.close()

        return summary

    async def list_admin_bots_with_stats(self, admin_telegram_id: int) -> list[AdminBotCard]:
        runtimes = await self._registry.list_admin_bots(admin_telegram_id)
        cards: list[AdminBotCard] = []
        for runtime in runtimes:
            users_total, dialogs_total, messages_total = await self._get_bot_totals(runtime.db_bot_id)
            cards.append(
                AdminBotCard(
                    runtime=runtime,
                    users_total=users_total,
                    dialogs_total=dialogs_total,
                    messages_total=messages_total,
                )
            )
        return cards

    async def toggle_bot(self, *, admin_telegram_id: int, db_bot_id: int) -> bool:
        return await self._registry.toggle_admin_bot(
            admin_telegram_id=admin_telegram_id,
            db_bot_id=db_bot_id,
        )

    async def get_dashboard(self, admin_telegram_id: int) -> AdminDashboard:
        async with self._session_factory() as session:
            base_query = (
                select(BotModel.id)
                .join(AdminAccount, AdminAccount.id == BotModel.owner_admin_id)
                .where(AdminAccount.telegram_id == admin_telegram_id)
            )
            bot_ids = [row[0] for row in (await session.execute(base_query)).all()]
            if not bot_ids:
                return AdminDashboard(
                    bots_total=0,
                    bots_active=0,
                    users_total=0,
                    dialogs_total=0,
                    messages_total=0,
                )

            bots_total_stmt = select(func.count(BotModel.id)).where(BotModel.id.in_(bot_ids))
            bots_active_stmt = select(func.count(BotModel.id)).where(
                BotModel.id.in_(bot_ids), BotModel.is_active.is_(True)
            )
            users_total_stmt = select(func.count(func.distinct(Dialog.user_id))).where(
                Dialog.bot_id.in_(bot_ids)
            )
            dialogs_total_stmt = select(func.count(Dialog.id)).where(Dialog.bot_id.in_(bot_ids))
            messages_total_stmt = select(func.count(MessageRecord.id)).where(
                MessageRecord.bot_id.in_(bot_ids)
            )

            return AdminDashboard(
                bots_total=int((await session.execute(bots_total_stmt)).scalar_one() or 0),
                bots_active=int((await session.execute(bots_active_stmt)).scalar_one() or 0),
                users_total=int((await session.execute(users_total_stmt)).scalar_one() or 0),
                dialogs_total=int((await session.execute(dialogs_total_stmt)).scalar_one() or 0),
                messages_total=int((await session.execute(messages_total_stmt)).scalar_one() or 0),
            )

    async def export_users_csv(self, admin_telegram_id: int) -> tuple[str, bytes]:
        async with self._session_factory() as session:
            stmt = (
                select(
                    BotModel.username,
                    User.telegram_id,
                    User.username,
                    User.first_name,
                    User.last_name,
                    User.language_code,
                    Dialog.created_at,
                )
                .join(Dialog, Dialog.bot_id == BotModel.id)
                .join(User, User.id == Dialog.user_id)
                .join(AdminAccount, AdminAccount.id == BotModel.owner_admin_id)
                .where(AdminAccount.telegram_id == admin_telegram_id)
                .order_by(Dialog.created_at.desc())
            )
            rows = (await session.execute(stmt)).all()

        buffer = StringIO()
        writer = csv.writer(buffer)
        writer.writerow(
            [
                "bot_username",
                "user_telegram_id",
                "username",
                "first_name",
                "last_name",
                "language_code",
                "dialog_created_at",
            ]
        )
        for row in rows:
            writer.writerow(row)

        payload = BytesIO(buffer.getvalue().encode("utf-8"))
        payload.seek(0)
        return "users_export.csv", payload.read()

    async def _get_bot_totals(self, bot_id: int) -> tuple[int, int, int]:
        async with self._session_factory() as session:
            users_stmt = select(func.count(func.distinct(Dialog.user_id))).where(Dialog.bot_id == bot_id)
            dialogs_stmt = select(func.count(Dialog.id)).where(Dialog.bot_id == bot_id)
            messages_stmt = select(func.count(MessageRecord.id)).where(MessageRecord.bot_id == bot_id)
            users_total = int((await session.execute(users_stmt)).scalar_one() or 0)
            dialogs_total = int((await session.execute(dialogs_stmt)).scalar_one() or 0)
            messages_total = int((await session.execute(messages_stmt)).scalar_one() or 0)
            return users_total, dialogs_total, messages_total
