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
    adder = update.message.from_user

    # Check if adder is admin (only needs to be done once per batch if we assume only one adder per message)
    adder_is_admin = False
    if adder:
        try:
            member = await context.bot.get_chat_member(chat_id, adder.id)
            if member.status in ["administrator", "creator"]:
                adder_is_admin = True
        except Exception as e:
            logger.error(f"Error checking admin status of adder {adder.id}: {e}")

    for user in new_users:
        user_id = user.id
        # If user added themselves (joined via link), adder.id == user.id.
        # If added by someone else, adder.id != user.id.
        # Requirement: "if user is added by an admin (not joined through link)" -> impl: added by admin != self.

        is_safe = False
        if adder and adder.id != user_id and adder_is_admin:
            is_safe = True
            logger.info(f"User {user_id} added by admin {adder.id}. Marking as safe.")

        add_user(
            user_id, chat_id, join_date=datetime.now(timezone.utc), is_safe=is_safe
        )
        logger.info(f"Added successfully {user_id} in {chat_id} (Safe: {is_safe})")
