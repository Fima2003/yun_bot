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
        logger.info("No message or user or chat. Returning.")
        return

    user = update.message.from_user
    chat = update.message.chat
    
    # Only check in groups/supergroups
    if chat.type not in ['group', 'supergroup']:
        logger.info("Not a group or supergroup. Returning.")
        return

    try:
        text = update.message.text or update.message.caption
        
        # Logic 1: Language Detection (First check as requested)
        is_russian = False
        if text and language_service.is_russian(text):
            is_russian = True
        
        if not is_russian:
            logger.info("Message not in Russian (or no text). Skipping checks.")
            return

        # Logic 2: Gemini Analysis (Only if Russian)
        # Prepare content for Gemini
        image_data = None
        if update.message.photo:
            # Get the largest photo
            photo = update.message.photo[-1]
            photo_file = await photo.get_file()
            image_byte_array = await photo_file.download_as_bytearray()
            image_data = bytes(image_byte_array)

        logger.info("Analyzing Russian message with Gemini...")
        scam_score = await gemini_service.analyze_content(text, image_data)
        logger.info(f"Gemini Scam Score: {scam_score}")

        # Logic 3: Action based on Scam Score
        if scam_score > SCAM_THRESHOLD:
            # Case: Russian AND Scam -> Delete & Ban
            logger.warning(f"Scam detected (Score: {scam_score}) in Russian message. Deleting and Banning.")
            try:
                await update.message.delete()
                await context.bot.ban_chat_member(chat_id=chat.id, user_id=user.id)
                logger.info(f"User {user.id} banned.")
            except Exception as e:
                logger.error(f"Failed to delete/ban: {e}")
        else:
            # Case: Russian BUT Not Scam -> Check User Age
            logger.info(f"Russian message detected but not scam (Score: {scam_score}). Checking user age...")
            
            is_new = await user_service.is_new_user(user.id, chat.id, context)
            
            if not is_new:
                logger.info("User is OLD. Allowing Russian message.")
                return

            # User is NEW -> Delete & Warn
            logger.info("User is NEW. Deleting and Warning.")
            try:
                # Reply first so the user sees it (if possible before delete, or tag them)
                await update.message.reply_text(
                    f"@{user.username or user.first_name} Будь ласка, спілкуйтеся Українською🇺🇦, Англійською🇬🇧 або Івритом🇮🇱!"
                )
                await update.message.delete()
            except Exception as e:
                logger.error(f"Failed to delete/warn: {e}")

    except Exception as e:
        logger.error(f"Error in scam_handler: {e}")
