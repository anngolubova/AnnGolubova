from __future__ import annotations

import logging

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramUnauthorizedError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
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
                indexed_tokens: list[tuple[int, str]] = []
                seen_tokens: set[str] = set()
                for index, token in enumerate(tokens):
                    if token in seen_tokens:
                        logger.warning(
                            "Duplicate token in BOT_TOKENS ignored at index=%s", index
                        )
                        continue
                    seen_tokens.add(token)
                    indexed_tokens.append((index, token))

                existing_by_token: dict[str, BotModel] = {}
                if indexed_tokens:
                    token_values = [token for _, token in indexed_tokens]
                    existing_stmt = select(BotModel).where(BotModel.token.in_(token_values))
                    existing_rows = (await session.execute(existing_stmt)).scalars().all()
                    existing_by_token = {row.token: row for row in existing_rows}

                for index, token in indexed_tokens:
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

                # If BOT_TOKENS is empty, all legacy bots must be deactivated.
                legacy_stmt = select(BotModel).where(BotModel.owner_admin_id.is_(None))
                legacy_rows = (await session.execute(legacy_stmt)).scalars().all()
                active_tokens = {token for _, token in indexed_tokens}
                for row in legacy_rows:
                    if row.token not in active_tokens:
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
                    welcome_text=bot_row.welcome_text,
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
        # Handle concurrent /start or button presses safely:
        # if another transaction inserts the same admin between SELECT and INSERT,
        # retry once and convert to update path.
        for attempt in range(2):
            async with self._session_factory() as session:
                try:
                    async with session.begin():
                        stmt = select(AdminAccount).where(
                            AdminAccount.telegram_id == telegram_id
                        ).limit(1)
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
                except IntegrityError:
                    if attempt == 0:
                        logger.warning(
                            "Admin upsert raced on telegram_id=%s, retrying once.",
                            telegram_id,
                        )
                        continue
                    raise

        raise RuntimeError("Admin upsert retry loop exited unexpectedly.")

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
                    welcome_text=row.welcome_text,
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
                    if existing.owner_admin_id == admin.id:
                        existing.username = username
                        existing.title = title or existing.title or username
                        existing.admin_chat_id = admin_telegram_id
                        existing.is_active = True
                        await session.flush()
                        return BotRuntime(
                            db_bot_id=existing.id,
                            token=existing.token,
                            username=existing.username,
                            title=existing.title,
                            welcome_text=existing.welcome_text,
                            admin_chat_id=existing.admin_chat_id,
                            owner_admin_telegram_id=admin_telegram_id,
                            is_active=bool(existing.is_active),
                        )
                    raise ValueError("Этот токен уже используется в системе.")

                existing_bot_id_stmt = select(BotModel).where(
                    BotModel.bot_telegram_id == bot_telegram_id
                ).limit(1)
                existing_by_bot_id = (
                    await session.execute(existing_bot_id_stmt)
                ).scalar_one_or_none()
                if existing_by_bot_id is not None:
                    if existing_by_bot_id.owner_admin_id == admin.id:
                        # Bot token rotation for the same owner.
                        existing_by_bot_id.token = token
                        existing_by_bot_id.username = username
                        existing_by_bot_id.title = title or existing_by_bot_id.title or username
                        existing_by_bot_id.admin_chat_id = admin_telegram_id
                        existing_by_bot_id.is_active = True
                        await session.flush()
                        return BotRuntime(
                            db_bot_id=existing_by_bot_id.id,
                            token=existing_by_bot_id.token,
                            username=existing_by_bot_id.username,
                            title=existing_by_bot_id.title,
                            welcome_text=existing_by_bot_id.welcome_text,
                            admin_chat_id=existing_by_bot_id.admin_chat_id,
                            owner_admin_telegram_id=admin_telegram_id,
                            is_active=bool(existing_by_bot_id.is_active),
                        )
                    raise ValueError("Этот бот уже принадлежит другому администратору.")

                try:
                    bot_row = BotModel(
                        owner_admin_id=admin.id,
                        token=token,
                        bot_telegram_id=bot_telegram_id,
                        username=username,
                        title=title or username,
                        welcome_text=None,
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
                        welcome_text=bot_row.welcome_text,
                        admin_chat_id=bot_row.admin_chat_id,
                        owner_admin_telegram_id=admin_telegram_id,
                        is_active=bool(bot_row.is_active),
                    )
                except IntegrityError as error:
                    raise ValueError(
                        "Не удалось сохранить бота. Проверьте уникальность токена и повторите."
                    ) from error

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

    async def bind_admin_chat_for_runtime(
        self,
        *,
        db_bot_id: int,
        actor_telegram_id: int | None,
        owner_admin_telegram_id: int | None,
        new_admin_chat_id: int,
    ) -> None:
        async with self._session_factory() as session:
            async with session.begin():
                bot_row = await session.get(BotModel, db_bot_id)
                if bot_row is None:
                    raise ValueError("Бот не найден.")
                self._assert_actor_can_manage_bot(
                    actor_telegram_id=actor_telegram_id,
                    owner_admin_telegram_id=owner_admin_telegram_id,
                    current_admin_chat_id=bot_row.admin_chat_id,
                )
                bot_row.admin_chat_id = new_admin_chat_id
                await session.flush()

    async def set_welcome_text_for_runtime(
        self,
        *,
        db_bot_id: int,
        actor_telegram_id: int | None,
        owner_admin_telegram_id: int | None,
        welcome_text: str,
    ) -> str:
        async with self._session_factory() as session:
            async with session.begin():
                bot_row = await session.get(BotModel, db_bot_id)
                if bot_row is None:
                    raise ValueError("Бот не найден.")
                self._assert_actor_can_manage_bot(
                    actor_telegram_id=actor_telegram_id,
                    owner_admin_telegram_id=owner_admin_telegram_id,
                    current_admin_chat_id=bot_row.admin_chat_id,
                )
                bot_row.welcome_text = welcome_text.strip()
                await session.flush()
                return bot_row.welcome_text

    def _assert_actor_can_manage_bot(
        self,
        *,
        actor_telegram_id: int | None,
        owner_admin_telegram_id: int | None,
        current_admin_chat_id: int,
    ) -> None:
        if actor_telegram_id is None:
            raise ValueError("Не удалось определить администратора команды.")
        if owner_admin_telegram_id is not None:
            if actor_telegram_id != owner_admin_telegram_id:
                raise ValueError("У вас нет прав управлять этим ботом.")
            return

        # Legacy fallback: allow current private admin chat owner to re-bind.
        if current_admin_chat_id > 0 and actor_telegram_id == current_admin_chat_id:
            return
        raise ValueError("Команда недоступна для этого пользователя.")

    async def _resolve_bot_identity(self, token: str) -> tuple[int, str | None]:
        temp_bot = Bot(token=token)
        try:
            me = await temp_bot.get_me()
            return me.id, me.username
        finally:
            await temp_bot.session.close()
            logger.info("Resolved bot identity for token ending with ...%s", token[-5:])
