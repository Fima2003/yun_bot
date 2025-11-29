import logging
from telegram import Update
from telegram.ext import ContextTypes
from config import SCAM_THRESHOLD
from bot.services.gemini_service import GeminiService
from bot.services.user_service import UserService
from bot.services.language_service import LanguageService

logger = logging.getLogger(__name__)

gemini_service = GeminiService()
user_service = UserService()
language_service = LanguageService()

async def handle_scam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles incoming messages and checks for scams if the user is new.
    """
    if not update.message or not update.message.from_user or not update.message.chat:
        return

    user = update.message.from_user
    chat = update.message.chat
    
    # Only check in groups/supergroups
    if chat.type not in ['group', 'supergroup']:
        return

    try:
        # Check if user is new
        is_new = await user_service.is_new_user(user.id, chat.id, context)
        
        # Logic 1: If NOT new (joined > 2 days), break/return
        if not is_new:
            return

        logger.info(f"New user detected. Analyzing message...")
        
        text = update.message.text or update.message.caption or ""
        image_data = None
        
        # Logic 2: Language Detection
        if text:
            if language_service.is_russian(text):
                logger.warning("Russian language detected. Deleting message.")
                try:
                    await update.message.delete()
                    # User requested "delete the message" for Russian. 
                    # Did not explicitly say "ban" for Russian, but said "delete".
                    # I will stick to delete only for now to be safe, or maybe ban?
                    # Request said: "If russian - delete the message."
                    return
                except Exception as e:
                    logger.error(f"Failed to delete Russian message: {e}")
                    return

        # Check for photos
        if update.message.photo:
            # Get the largest photo
            photo = update.message.photo[-1]
            file = await context.bot.get_file(photo.file_id)
            image_byte_array = await file.download_as_bytearray()
            image_data = bytes(image_byte_array)

        if not text and not image_data:
            return

        # Logic 3: Gemini Analysis
        scam_score = await gemini_service.analyze_content(text, image_data)
        logger.info(f"Scam score: {scam_score}")

        if scam_score > SCAM_THRESHOLD:
            logger.warning(f"Scam detected! Score: {scam_score}. Deleting message and banning user.")
            try:
                await update.message.delete()
                await context.bot.ban_chat_member(chat.id, user.id)
                logger.info(f"User {user.id} banned.")
            except Exception as e:
                logger.error(f"Failed to delete message or ban user: {e}")

    except Exception as e:
        logger.error(f"Error in scam_handler: {e}")
