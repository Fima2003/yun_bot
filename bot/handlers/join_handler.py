import logging
from datetime import datetime, timezone
from telegram import Update, ChatMember
from telegram.ext import ContextTypes
from db.core import add_user

logger = logging.getLogger(__name__)

async def join_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles new chat members and adds them to the database.
    """
    new_users = update.message.new_chat_members
    logger.info(f"New users: {new_users}")
    if not new_users:
        return

    chat_id = update.message.chat.id
    for user in new_users:
        user_id = user.id
        add_user(user_id, chat_id, join_date=datetime.now(timezone.utc), is_safe=False)
        logger.info(f"Added successfully {user_id} in {chat_id}")
