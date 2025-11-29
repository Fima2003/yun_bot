from telegram import Update
from telegram.ext import ContextTypes
import logging

logger = logging.getLogger(__name__)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Responds to /start command.
    """
    logger.info("User %s started the bot", update.effective_user.id or "Unknown")
    await update.message.reply_text("Вітаю, Юначе!")