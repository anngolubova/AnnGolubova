from __future__ import annotations

import logging

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramUnauthorizedError
from sqlalchemy import and_, not_, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from bot.runtime import BotRuntime
from database.models import AdminAccount, BotModel

logger = logging.getLogger(__name__)


class BotRegistryService:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self._session_factory = session_factory

    async def sync_from_tokens(
        self,
        *,
        tokens: list[str],
        default_admin_chat_id: int | None,
        bot_admin_chat_ids: list[int],
    ) -> None:
        async with self._session_factory() as session:
            async with session.begin():
                if not tokens:
                    return

                existing_stmt = select(BotModel).where(BotModel.token.in_(tokens))
                existing_rows = (await session.execute(existing_stmt)).scalars().all()
                existing_by_token = {row.token: row for row in existing_rows}

                for index, token in enumerate(tokens):
                    admin_chat_id = (
                        bot_admin_chat_ids[index]
                        if index < len(bot_admin_chat_ids)
                        else default_admin_chat_id
                    )
                    if admin_chat_id is None:
                        raise ValueError(
                            "ADMIN_CHAT_ID is required when BOT_ADMIN_CHAT_IDS is incomplete."
                        )

                    bot_telegram_id, username = await self._resolve_bot_identity(token)
                    bot_record = existing_by_token.get(token)
                    if bot_record is None:
                        session.add(
                            BotModel(
                                token=token,
                                bot_telegram_id=bot_telegram_id,
                                username=username,
                                title=username,
                                admin_chat_id=admin_chat_id,
                                is_active=True,
                            )
                        )
                    else:
                        bot_record.is_active = True
                        if bot_record.owner_admin_id is None:
                            bot_record.bot_telegram_id = bot_telegram_id
                            bot_record.username = username
                            bot_record.title = bot_record.title or username
                            bot_record.admin_chat_id = admin_chat_id

                deactivate_stmt = select(BotModel).where(
                    and_(
                        BotModel.owner_admin_id.is_(None),
                        not_(BotModel.token.in_(tokens)),
                    )
                )
                for row in (await session.execute(deactivate_stmt)).scalars().all():
                    row.is_active = False

    async def get_active_bots(self) -> list[BotRuntime]:
        async with self._session_factory() as session:
            stmt = (
                select(BotModel, AdminAccount.telegram_id)
                .outerjoin(AdminAccount, AdminAccount.id == BotModel.owner_admin_id)
                .where(BotModel.is_active.is_(True))
            )
            rows = (await session.execute(stmt)).all()
            return [
                BotRuntime(
                    db_bot_id=bot_row.id,
                    token=bot_row.token,
                    username=bot_row.username,
                    title=bot_row.title,
                    admin_chat_id=bot_row.admin_chat_id,
                    owner_admin_telegram_id=owner_admin_telegram_id,
                    is_active=bool(bot_row.is_active),
                )
                for bot_row, owner_admin_telegram_id in rows
            ]

    async def upsert_admin(
        self,
        *,
        telegram_id: int,
        username: str | None,
        first_name: str | None,
        last_name: str | None,
    ) -> AdminAccount:
        async with self._session_factory() as session:
            async with session.begin():
                stmt = select(AdminAccount).where(AdminAccount.telegram_id == telegram_id).limit(1)
                admin = (await session.execute(stmt)).scalar_one_or_none()
                if admin is None:
                    admin = AdminAccount(
                        telegram_id=telegram_id,
                        username=username,
                        first_name=first_name,
                        last_name=last_name,
                        is_active=True,
                    )
                    session.add(admin)
                    await session.flush()
                    return admin

                admin.username = username
                admin.first_name = first_name
                admin.last_name = last_name
                admin.is_active = True
                await session.flush()
                return admin

    async def list_admin_bots(self, admin_telegram_id: int) -> list[BotRuntime]:
        async with self._session_factory() as session:
            stmt = (
                select(BotModel)
                .join(AdminAccount, AdminAccount.id == BotModel.owner_admin_id)
                .where(AdminAccount.telegram_id == admin_telegram_id)
                .order_by(BotModel.id.desc())
            )
            rows = (await session.execute(stmt)).scalars().all()
            return [
                BotRuntime(
                    db_bot_id=row.id,
                    token=row.token,
                    username=row.username,
                    title=row.title,
                    admin_chat_id=row.admin_chat_id,
                    owner_admin_telegram_id=admin_telegram_id,
                    is_active=bool(row.is_active),
                )
                for row in rows
            ]

    async def add_bot_for_admin(
        self,
        *,
        admin_telegram_id: int,
        token: str,
        title: str | None,
    ) -> BotRuntime:
        try:
            bot_telegram_id, username = await self._resolve_bot_identity(token)
        except (TelegramUnauthorizedError, TelegramBadRequest) as error:
            raise ValueError("Невалидный токен бота. Проверьте токен из @BotFather.") from error

        async with self._session_factory() as session:
            async with session.begin():
                admin_stmt = select(AdminAccount).where(
                    AdminAccount.telegram_id == admin_telegram_id
                ).limit(1)
                admin = (await session.execute(admin_stmt)).scalar_one_or_none()
                if admin is None:
                    raise ValueError("Admin profile was not found. Run /start first.")

                existing_stmt = select(BotModel).where(BotModel.token == token).limit(1)
                existing = (await session.execute(existing_stmt)).scalar_one_or_none()
                if existing is not None:
                    raise ValueError("Этот токен уже используется в системе.")

                bot_row = BotModel(
                    owner_admin_id=admin.id,
                    token=token,
                    bot_telegram_id=bot_telegram_id,
                    username=username,
                    title=title or username,
                    admin_chat_id=admin_telegram_id,
                    is_active=True,
                )
                session.add(bot_row)
                await session.flush()
                return BotRuntime(
                    db_bot_id=bot_row.id,
                    token=bot_row.token,
                    username=bot_row.username,
                    title=bot_row.title,
                    admin_chat_id=bot_row.admin_chat_id,
                    owner_admin_telegram_id=admin_telegram_id,
                    is_active=bool(bot_row.is_active),
                )

    async def toggle_admin_bot(
        self,
        *,
        admin_telegram_id: int,
        db_bot_id: int,
    ) -> bool:
        async with self._session_factory() as session:
            async with session.begin():
                stmt = (
                    select(BotModel)
                    .join(AdminAccount, AdminAccount.id == BotModel.owner_admin_id)
                    .where(AdminAccount.telegram_id == admin_telegram_id, BotModel.id == db_bot_id)
                    .limit(1)
                )
                bot_row = (await session.execute(stmt)).scalar_one_or_none()
                if bot_row is None:
                    raise ValueError("Бот не найден или не принадлежит этому администратору.")

                bot_row.is_active = not bot_row.is_active
                await session.flush()
                return bool(bot_row.is_active)

    async def _resolve_bot_identity(self, token: str) -> tuple[int, str | None]:
        temp_bot = Bot(token=token)
        try:
            me = await temp_bot.get_me()
            return me.id, me.username
        finally:
            await temp_bot.session.close()
            logger.info("Resolved bot identity for token ending with ...%s", token[-5:])
