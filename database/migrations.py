from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine


async def run_sqlite_compat_migrations(engine: AsyncEngine) -> None:
    async with engine.begin() as conn:
        if conn.dialect.name != "sqlite":
            return

        tables_result = await conn.execute(
            text("SELECT name FROM sqlite_master WHERE type = 'table'")
        )
        existing_tables = {row[0] for row in tables_result.fetchall()}

        if "admins" not in existing_tables:
            await conn.execute(
                text(
                    """
                    CREATE TABLE admins (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        telegram_id BIGINT NOT NULL UNIQUE,
                        username VARCHAR(255),
                        first_name VARCHAR(255),
                        last_name VARCHAR(255),
                        is_active BOOLEAN NOT NULL DEFAULT 1,
                        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                    )
                    """
                )
            )
            await conn.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS ix_admins_telegram_id ON admins (telegram_id)"
                )
            )

        if "bots" in existing_tables:
            columns_result = await conn.execute(text("PRAGMA table_info('bots')"))
            existing_columns = {row[1] for row in columns_result.fetchall()}

            if "owner_admin_id" not in existing_columns:
                await conn.execute(text("ALTER TABLE bots ADD COLUMN owner_admin_id INTEGER"))
                await conn.execute(
                    text(
                        "CREATE INDEX IF NOT EXISTS ix_bots_owner_admin_id ON bots (owner_admin_id)"
                    )
                )

            if "title" not in existing_columns:
                await conn.execute(text("ALTER TABLE bots ADD COLUMN title VARCHAR(255)"))

            if "welcome_text" not in existing_columns:
                await conn.execute(text("ALTER TABLE bots ADD COLUMN welcome_text TEXT"))
