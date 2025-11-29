import logging
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

async def added_to_group_chat_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles the bot being added to a group chat.
    """
    logger.info("Bot added to group chat")