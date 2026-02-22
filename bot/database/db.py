"""Асинхронная работа с PostgreSQL для статистики бота."""
import logging
from datetime import datetime, timezone
import asyncpg
from bot.config import get_database_url

logger = logging.getLogger(__name__)
_pool: asyncpg.Pool | None = None

async def get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(get_database_url(), min_size=1, max_size=5, command_timeout=60)
        logger.info("Пул подключений к БД создан")
    return _pool

async def close_pool() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None
        logger.info("Пул подключений к БД закрыт")

async def init_db() -> None:
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""CREATE TABLE IF NOT EXISTS user_chat_stats (id SERIAL PRIMARY KEY, chat_id BIGINT NOT NULL, user_id BIGINT NOT NULL, message_count INT NOT NULL DEFAULT 0, last_activity_at TIMESTAMP WITH TIME ZONE, created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, UNIQUE(chat_id, user_id))""")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_user_chat_stats_chat_id ON user_chat_stats(chat_id)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_user_chat_stats_user_id ON user_chat_stats(user_id)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_user_chat_stats_last_activity ON user_chat_stats(last_activity_at DESC)")
        await conn.execute("""CREATE TABLE IF NOT EXISTS messages (id SERIAL PRIMARY KEY, chat_id BIGINT NOT NULL, user_id BIGINT NOT NULL, message_id BIGINT NOT NULL, text TEXT, message_type VARCHAR(50) NOT NULL DEFAULT 'text', created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP)""")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_messages_chat_id ON messages(chat_id)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_messages_user_id ON messages(user_id)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at DESC)")
        await conn.execute("""CREATE TABLE IF NOT EXISTS bot_logs (id SERIAL PRIMARY KEY, created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, level VARCHAR(10) NOT NULL, logger_name VARCHAR(255) NOT NULL, message TEXT NOT NULL)""")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_bot_logs_created_at ON bot_logs(created_at DESC)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_bot_logs_level ON bot_logs(level)")
    logger.info("Схема БД проверена/создана")

async def record_message(chat_id: int, user_id: int) -> None:
    pool = await get_pool()
    now = datetime.now(timezone.utc)
    async with pool.acquire() as conn:
        await conn.execute("""INSERT INTO user_chat_stats (chat_id, user_id, message_count, last_activity_at, updated_at) VALUES ($1, $2, 1, $3, $3) ON CONFLICT (chat_id, user_id) DO UPDATE SET message_count = user_chat_stats.message_count + 1, last_activity_at = $3, updated_at = $3""", chat_id, user_id, now)

async def insert_message(chat_id: int, user_id: int, message_id: int, text: str | None, message_type: str, created_at: datetime | None = None) -> None:
    if created_at is None:
        created_at = datetime.now(timezone.utc)
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("INSERT INTO messages (chat_id, user_id, message_id, text, message_type, created_at) VALUES ($1, $2, $3, $4, $5, $6)", chat_id, user_id, message_id, (text or "")[:10000], (message_type or "text")[:50], created_at)

async def get_user_stats(user_id: int) -> tuple[int, datetime | None]:
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT COALESCE(SUM(message_count), 0)::int AS total, MAX(last_activity_at) AS last_activity FROM user_chat_stats WHERE user_id = $1", user_id)
    if not row:
        return 0, None
    return row["total"], row["last_activity"]

async def get_user_stats_in_chat(chat_id: int, user_id: int) -> tuple[int, datetime | None]:
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT message_count, last_activity_at FROM user_chat_stats WHERE chat_id = $1 AND user_id = $2", chat_id, user_id)
    if not row:
        return 0, None
    return row["message_count"], row["last_activity_at"]

async def get_last_message_in_chat(chat_id: int, user_id: int) -> tuple[str | None, str] | None:
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT text, message_type FROM messages WHERE chat_id = $1 AND user_id = $2 ORDER BY created_at DESC LIMIT 1", chat_id, user_id)
    if not row:
        return None
    return (row["text"] or None, row["message_type"] or "text")

async def get_top_users(chat_id: int, limit: int = 10) -> list[tuple[int, int, datetime | None]]:
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT user_id, message_count, last_activity_at FROM user_chat_stats WHERE chat_id = $1 ORDER BY message_count DESC, last_activity_at DESC NULLS LAST LIMIT $2", chat_id, limit)
    return [(r["user_id"], r["message_count"], r["last_activity_at"]) for r in rows]

async def insert_log(level: str, logger_name: str, message: str) -> None:
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("INSERT INTO bot_logs (level, logger_name, message) VALUES ($1, $2, $3)", level[:10], logger_name[:255] or "", message[:10000] or "")
