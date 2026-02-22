"""Команда /stats."""
import logging
from datetime import timezone

from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

from bot.database import get_user_stats, get_user_stats_in_chat, get_last_message_in_chat

logger = logging.getLogger(__name__)
router = Router(name="stats")

def _format_last_activity(dt):
    if dt is None:
        return "—"
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.strftime("%d.%m.%Y %H:%M UTC")

@router.message(Command("stats"))
async def cmd_stats(message: Message) -> None:
    user = message.from_user
    if not user:
        return
    try:
        is_group = message.chat.type in ("group", "supergroup")
        if is_group:
            in_chat, last_chat = await get_user_stats_in_chat(message.chat.id, user.id)
            last_msg = await get_last_message_in_chat(message.chat.id, user.id)
            if last_msg:
                msg_text, msg_type = last_msg
                last_msg_line = msg_text.replace("<", "&lt;").replace(">", "&gt;")[:300] + ("..." if msg_text and len(msg_text) > 300 else "") if msg_text else f"[{msg_type}]"
            else:
                last_msg_line = "—"
            text = "📊 <b>Ваша статистика</b>\n\nВ этом чате: <b>%s</b> сообщ.\nПоследняя активность: <b>%s</b>\n\nПоследнее сообщение: <i>%s</i>" % (in_chat, _format_last_activity(last_chat), last_msg_line)
        else:
            total, last_total = await get_user_stats(user.id)
            text = "📊 <b>Ваша статистика</b>\n\nВсего сообщений: <b>%s</b>\nПоследняя активность: <b>%s</b>" % (total, _format_last_activity(last_total))
        await message.answer(text)
    except Exception as e:
        logger.exception("Ошибка при получении статистики: %s", e)
        await message.answer("Произошла ошибка при получении статистики. Попробуйте позже.")
