from telegram.ext._application import Application
from bot.handlers.added_to_group_chat_handler import added_to_group_chat_handler
from telegram.ext.filters import StatusUpdate
from telegram.ext.filters import TEXT, PHOTO, CAPTION
from bot.handlers.scam_handler import handle_scam
from bot.handlers.start import start_command
from bot.handlers.join_handler import join_handler
from bot.handlers.admin import add_user_command

import logging
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    CommandHandler,
    ChatMemberHandler,
)
from config import (
    TELEGRAM_BOT_TOKEN,
    CLEANUP_CHAT_ID,
    CLEANUP_MESSAGE_ID,
    CLEANUP_USER_ID,
)
from db.core import increment_blocked_count

logger = logging.getLogger(__name__)


async def post_init(application: Application):
    """
    Runs after the bot application is initialized.
    Used for one-time startup tasks like cleaning up a specific message.
    """
    if (CLEANUP_CHAT_ID and CLEANUP_CHAT_ID.strip() != "") and (
        CLEANUP_MESSAGE_ID and CLEANUP_MESSAGE_ID.strip() != ""
    ):
        logger.info(
            f"Running startup cleanup for Chat: {CLEANUP_CHAT_ID}, Msg: {CLEANUP_MESSAGE_ID}"
        )
        try:
            # Attempt delete
            await application.bot.delete_message(
                chat_id=CLEANUP_CHAT_ID, message_id=int(CLEANUP_MESSAGE_ID)
            )
            logger.info("Startup cleanup: Message deleted.")
        except Exception as e:
            logger.error(f"Startup cleanup: Failed to delete message: {e}")

        if CLEANUP_USER_ID:
            try:
                # Attempt ban
                await application.bot.ban_chat_member(
                    chat_id=CLEANUP_CHAT_ID, user_id=CLEANUP_USER_ID
                )
                increment_blocked_count()
                logger.info(f"Startup cleanup: User {CLEANUP_USER_ID} banned.")
            except Exception as e:
                logger.error(f"Startup cleanup: Failed to ban user: {e}")


def run_bot():
    if not TELEGRAM_BOT_TOKEN:
        logger.error("Error: TELEGRAM_BOT_TOKEN not found. Please set it in .env file.")
        exit(1)

    application = (
        ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).post_init(post_init).build()
    )

    # Handle /start command
    application.add_handler(
        CommandHandler("start", start_command),
    )

    # Handle /stats command
    application.add_handler(
        CommandHandler("stats", stats_command),
    )

    # Handle new members
    application.add_handler(MessageHandler(StatusUpdate.NEW_CHAT_MEMBERS, join_handler))

    # Handle text messages and messages with photos/captions
    application.add_handler(MessageHandler(TEXT | PHOTO | CAPTION, handle_scam))

    application.add_handler(
        ChatMemberHandler(added_to_group_chat_handler, ChatMemberHandler.MY_CHAT_MEMBER)
    )

    # Handle /add_user command (Admin only)
    application.add_handler(
        CommandHandler("add_user", add_user_command),
    )

    logger.info("Bot is running now...")
    application.run_polling()
