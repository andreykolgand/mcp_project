-- Таблица статистики по пользователям в чатах для бота
CREATE TABLE IF NOT EXISTS user_chat_stats (
    id          SERIAL PRIMARY KEY,
    chat_id     BIGINT NOT NULL,
    user_id     BIGINT NOT NULL,
    message_count INT NOT NULL DEFAULT 0,
    last_activity_at TIMESTAMP WITH TIME ZONE,
    created_at  TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(chat_id, user_id)
);
CREATE INDEX IF NOT EXISTS idx_user_chat_stats_chat_id ON user_chat_stats(chat_id);
CREATE INDEX IF NOT EXISTS idx_user_chat_stats_user_id ON user_chat_stats(user_id);
CREATE INDEX IF NOT EXISTS idx_user_chat_stats_last_activity ON user_chat_stats(last_activity_at DESC);
COMMENT ON TABLE user_chat_stats IS 'Статистика сообщений пользователей в чатах для Telegram-бота';

CREATE TABLE IF NOT EXISTS messages (
    id          SERIAL PRIMARY KEY,
    chat_id     BIGINT NOT NULL,
    user_id     BIGINT NOT NULL,
    message_id  BIGINT NOT NULL,
    text        TEXT,
    message_type VARCHAR(50) NOT NULL DEFAULT 'text',
    created_at  TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_messages_chat_id ON messages(chat_id);
CREATE INDEX IF NOT EXISTS idx_messages_user_id ON messages(user_id);
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at DESC);
COMMENT ON TABLE messages IS 'Сообщения пользователей в чатах (текст, тип, дата)';

CREATE TABLE IF NOT EXISTS bot_logs (
    id          SERIAL PRIMARY KEY,
    created_at  TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    level       VARCHAR(10) NOT NULL,
    logger_name VARCHAR(255) NOT NULL,
    message     TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_bot_logs_created_at ON bot_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_bot_logs_level ON bot_logs(level);
COMMENT ON TABLE bot_logs IS 'Логи работы Telegram-бота';
