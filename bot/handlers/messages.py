"""Обработка входящих сообщений и событий чата."""
import logging
from datetime import timezone

from aiogram import Router, F
from aiogram.types import Message, ChatMemberUpdated

from bot.database import record_message, insert_message

logger = logging.getLogger(__name__)
router = Router(name="messages")

def _message_text(msg: Message) -> str | None:
    if msg.text:
        return msg.text
    if msg.caption:
        return msg.caption
    return None

def _message_type(msg: Message) -> str:
    return getattr(msg, "content_type", None) or "text"

@router.message(F.chat.type.in_({"group", "supergroup"}))
async def on_group_message(message: Message) -> None:
    if message.from_user and message.from_user.is_bot:
        return
    if not message.from_user:
        return
    try:
        await record_message(chat_id=message.chat.id, user_id=message.from_user.id)
        msg_date = message.date
        if msg_date and msg_date.tzinfo is None:
            msg_date = msg_date.replace(tzinfo=timezone.utc)
        await insert_message(chat_id=message.chat.id, user_id=message.from_user.id, message_id=message.message_id, text=_message_text(message), message_type=_message_type(message), created_at=msg_date)
    except Exception as e:
        logger.exception("Ошибка при записи сообщения в БД: %s", e)

@router.my_chat_member()
async def on_my_chat_member(event: ChatMemberUpdated) -> None:
    old, new, chat = event.old_chat_member, event.new_chat_member, event.chat
    if event.chat.type not in ("group", "supergroup"):
        return
    if new.user.id == event.bot.id:
        if old.status in ("left", "kicked") and new.status in ("member", "administrator"):
            logger.info("Бот добавлен в чат: chat_id=%s title=%s", chat.id, getattr(chat, "title", ""))
        elif old.status in ("member", "administrator") and new.status in ("left", "kicked"):
            logger.info("Бот удалён из чата: chat_id=%s title=%s", chat.id, getattr(chat, "title", ""))
        return
    if old.status in ("left", "kicked") and new.status in ("member", "administrator"):
        user = new.user
        logger.info("Пользователь вступил в группу: chat_id=%s user_id=%s username=%s", chat.id, user.id, getattr(user, "username", None))
