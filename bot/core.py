from bot.handlers.added_to_group_chat_handler import added_to_group_chat_handler
from telegram.ext.filters import StatusUpdate
from telegram.ext.filters import TEXT, PHOTO, CAPTION
from bot.handlers.handlers import handle_scam
from bot.handlers.start import start_command
from bot.handlers.join_handler import join_handler
import logging
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, ChatMemberHandler
from config import TELEGRAM_BOT_TOKEN

logger = logging.getLogger(__name__)

def run_bot():
    if not TELEGRAM_BOT_TOKEN:
        logger.error("Error: TELEGRAM_BOT_TOKEN not found. Please set it in .env file.")
        exit(1)

    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Handle /start command
    application.add_handler(
        CommandHandler('start', start_command),
    )

    # Handle new members
    application.add_handler(
        MessageHandler(StatusUpdate.NEW_CHAT_MEMBERS, join_handler)
    )

    # Handle text messages and messages with photos/captions
    application.add_handler(
        MessageHandler(TEXT | PHOTO | CAPTION, handle_scam)
    )

    application.add_handler(
        ChatMemberHandler(added_to_group_chat_handler, ChatMemberHandler.MY_CHAT_MEMBER)
    )
    
    logger.info("Bot is running now...")
    application.run_polling()
