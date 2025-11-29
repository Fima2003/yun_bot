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
        print("Error: TELEGRAM_BOT_TOKEN not found. Please set it in .env file.")
        exit(1)

    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Handle /start command
    start_handler = CommandHandler('start', start_command)
    application.add_handler(start_handler)

    # Handle new members
    join_member_handler = MessageHandler(StatusUpdate.NEW_CHAT_MEMBERS, join_handler)
    application.add_handler(join_member_handler)

    # Handle text messages and messages with photos/captions
    scam_handler = MessageHandler(TEXT | PHOTO | CAPTION, handle_scam)
    application.add_handler(scam_handler)
    
    print("Bot is running...")
    application.run_polling()
