from __future__ import annotations

from enum import Enum

from sqlalchemy import BigInteger, Boolean, Enum as SqlEnum, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base, TimestampMixin


class DialogStatus(str, Enum):
    OPEN = "open"
    CLOSED = "closed"


class MessageDirection(str, Enum):
    USER_TO_ADMIN = "user_to_admin"
    ADMIN_TO_USER = "admin_to_user"
    BROADCAST = "broadcast"


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True, nullable=False)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    first_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    language_code: Mapped[str | None] = mapped_column(String(16), nullable=True)
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    dialogs = relationship("Dialog", back_populates="user")


class BotModel(TimestampMixin, Base):
    __tablename__ = "bots"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    token: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    bot_telegram_id: Mapped[int | None] = mapped_column(BigInteger, unique=True, nullable=True)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    admin_chat_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    dialogs = relationship("Dialog", back_populates="bot")


class Dialog(TimestampMixin, Base):
    __tablename__ = "dialogs"
    __table_args__ = (UniqueConstraint("bot_id", "user_id", name="uq_dialogs_bot_user"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    bot_id: Mapped[int] = mapped_column(ForeignKey("bots.id", ondelete="CASCADE"), index=True, nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    status: Mapped[DialogStatus] = mapped_column(
        SqlEnum(DialogStatus, name="dialog_status_enum"),
        default=DialogStatus.OPEN,
        nullable=False,
    )
    thread_root_admin_message_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    user = relationship("User", back_populates="dialogs")
    bot = relationship("BotModel", back_populates="dialogs")
    messages = relationship("MessageRecord", back_populates="dialog")


class MessageRecord(TimestampMixin, Base):
    __tablename__ = "messages"
    __table_args__ = (
        Index("ix_messages_target_lookup", "bot_id", "target_chat_id", "target_message_id"),
        Index("ix_messages_source_lookup", "bot_id", "source_chat_id", "source_message_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    bot_id: Mapped[int] = mapped_column(ForeignKey("bots.id", ondelete="CASCADE"), index=True, nullable=False)
    dialog_id: Mapped[int] = mapped_column(ForeignKey("dialogs.id", ondelete="CASCADE"), index=True, nullable=False)
    direction: Mapped[MessageDirection] = mapped_column(
        SqlEnum(MessageDirection, name="message_direction_enum"),
        nullable=False,
    )
    content_type: Mapped[str] = mapped_column(String(32), nullable=False)

    source_chat_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    source_message_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    target_chat_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    target_message_id: Mapped[int] = mapped_column(BigInteger, nullable=False)

    dialog = relationship("Dialog", back_populates="messages")
