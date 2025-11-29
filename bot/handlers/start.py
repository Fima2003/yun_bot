from telegram import Update
from telegram.ext import ContextTypes

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Responds to /start command.
    """
    await update.message.reply_text("Вітаю, Юначе!")