from telegram import Update
from telegram.ext import ContextTypes
from db.core import get_blocked_count

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles the /stats command.
    """
    count = get_blocked_count()
    await update.message.reply_text(f"🚫 Заблоковано ботів: {count}")
