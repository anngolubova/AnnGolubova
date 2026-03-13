from __future__ import annotations

from dataclasses import dataclass

from aiogram.types import User as TelegramUser
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from database.models import Dialog, MessageDirection, MessageRecord, User


@dataclass(slots=True)
class DialogContext:
    dialog_id: int
    user_db_id: int
    user_telegram_id: int
    thread_root_admin_message_id: int | None
    is_new_dialog: bool


@dataclass(slots=True)
class DialogTarget:
    dialog_id: int
    user_telegram_id: int


class DialogService:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession], bot_id: int):
        self._session_factory = session_factory
        self._bot_id = bot_id

    async def get_or_create_dialog_context(self, tg_user: TelegramUser) -> DialogContext:
        async with self._session_factory() as session:
            async with session.begin():
                user = await self._get_or_create_user(session, tg_user)
                dialog = await self._get_dialog(session, user.id)
                is_new_dialog = False

                if dialog is None:
                    dialog = Dialog(bot_id=self._bot_id, user_id=user.id)
                    session.add(dialog)
                    await session.flush()
                    is_new_dialog = True

                return DialogContext(
                    dialog_id=dialog.id,
                    user_db_id=user.id,
                    user_telegram_id=user.telegram_id,
                    thread_root_admin_message_id=dialog.thread_root_admin_message_id,
                    is_new_dialog=is_new_dialog,
                )

    async def save_user_to_admin_message(
        self,
        *,
        dialog_id: int,
        content_type: str,
        source_chat_id: int,
        source_message_id: int,
        target_chat_id: int,
        target_message_id: int,
        set_thread_root: bool,
    ) -> None:
        async with self._session_factory() as session:
            async with session.begin():
                message = MessageRecord(
                    bot_id=self._bot_id,
                    dialog_id=dialog_id,
                    direction=MessageDirection.USER_TO_ADMIN,
                    content_type=content_type,
                    source_chat_id=source_chat_id,
                    source_message_id=source_message_id,
                    target_chat_id=target_chat_id,
                    target_message_id=target_message_id,
                )
                session.add(message)

                if set_thread_root:
                    dialog = await session.get(Dialog, dialog_id)
                    if dialog is not None and dialog.thread_root_admin_message_id is None:
                        dialog.thread_root_admin_message_id = target_message_id

    async def resolve_dialog_by_admin_message(
        self,
        *,
        admin_chat_id: int,
        admin_message_id: int,
    ) -> DialogTarget | None:
        async with self._session_factory() as session:
            statement = (
                select(Dialog.id, User.telegram_id)
                .join(MessageRecord, MessageRecord.dialog_id == Dialog.id)
                .join(User, User.id == Dialog.user_id)
                .where(Dialog.bot_id == self._bot_id)
                .where(
                    or_(
                        and_(
                            MessageRecord.target_chat_id == admin_chat_id,
                            MessageRecord.target_message_id == admin_message_id,
                        ),
                        and_(
                            MessageRecord.source_chat_id == admin_chat_id,
                            MessageRecord.source_message_id == admin_message_id,
                        ),
                    )
                )
                .order_by(MessageRecord.id.desc())
                .limit(1)
            )
            row = (await session.execute(statement)).first()
            if row is None:
                return None
            return DialogTarget(dialog_id=row[0], user_telegram_id=row[1])

    async def save_admin_to_user_message(
        self,
        *,
        dialog_id: int,
        content_type: str,
        source_chat_id: int,
        source_message_id: int,
        target_chat_id: int,
        target_message_id: int,
    ) -> None:
        async with self._session_factory() as session:
            async with session.begin():
                message = MessageRecord(
                    bot_id=self._bot_id,
                    dialog_id=dialog_id,
                    direction=MessageDirection.ADMIN_TO_USER,
                    content_type=content_type,
                    source_chat_id=source_chat_id,
                    source_message_id=source_message_id,
                    target_chat_id=target_chat_id,
                    target_message_id=target_message_id,
                )
                session.add(message)

    async def _get_or_create_user(self, session: AsyncSession, tg_user: TelegramUser) -> User:
        statement = select(User).where(User.telegram_id == tg_user.id).limit(1)
        user = (await session.execute(statement)).scalar_one_or_none()
        if user is None:
            user = User(
                telegram_id=tg_user.id,
                username=tg_user.username,
                first_name=tg_user.first_name,
                last_name=tg_user.last_name,
                language_code=tg_user.language_code,
            )
            session.add(user)
            await session.flush()
            return user

        user.username = tg_user.username
        user.first_name = tg_user.first_name
        user.last_name = tg_user.last_name
        user.language_code = tg_user.language_code
        return user

    async def _get_dialog(self, session: AsyncSession, user_db_id: int) -> Dialog | None:
        statement = (
            select(Dialog)
            .where(Dialog.bot_id == self._bot_id, Dialog.user_id == user_db_id)
            .limit(1)
        )
        return (await session.execute(statement)).scalar_one_or_none()
