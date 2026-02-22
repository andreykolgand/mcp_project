"""Команда /top (только для админов)."""
import logging
from datetime import timezone

from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command

from bot.config import ADMIN_IDS
from bot.database import get_top_users

logger = logging.getLogger(__name__)
router = Router(name="top")

def _format_datetime(dt):
    if dt is None:
        return "—"
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.strftime("%d.%m.%Y %H:%M")

def _display_name(user) -> str:
    if user.username:
        return f"@{user.username}"
    if user.first_name or user.last_name:
        return " ".join(filter(None, (user.first_name, user.last_name))).strip()
    return f"id{user.id}"

@router.message(Command("top"), F.chat.type.in_({"group", "supergroup"}))
async def cmd_top(message: Message) -> None:
    user = message.from_user
    if not user or user.id not in ADMIN_IDS:
        return
    try:
        chat_id = message.chat.id
        try:
            total_members = await message.bot.get_chat_member_count(chat_id)
            members_without_bot = max(0, total_members - 1)
        except Exception:
            members_without_bot = None
        top = await get_top_users(chat_id=chat_id, limit=10)
        if not top:
            await message.reply("В этом чате пока нет учтённой активности.")
            return
        lines = ["🏆 <b>Топ-10 активных пользователей</b>\n"]
        if members_without_bot is not None:
            lines.append(f"👥 Участников в группе: <b>{members_without_bot}</b> (без бота)\n")
        for i, (uid, count, last_at) in enumerate(top, 1):
            last_str = _format_datetime(last_at)
            try:
                member = await message.bot.get_chat_member(chat_id, uid)
                name = _display_name(member.user)
            except Exception:
                name = f"id{uid}"
            lines.append(f"{i}. {name} — <b>{count}</b> сообщ. (последнее: {last_str})")
        await message.reply("\n".join(lines))
    except Exception as e:
        logger.exception("Ошибка при получении топа: %s", e)
        await message.reply("Произошла ошибка при формировании топа. Попробуйте позже.")
