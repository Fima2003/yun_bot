import logging
from telegram import Update
from telegram.ext import ContextTypes
from config import SCAM_THRESHOLD
from bot.services.gemini_service import GeminiService
from bot.services.user_service import UserService
from bot.services.language_service import LanguageService
from db.core import get_user, increment_message_count, increment_blocked_count

logger = logging.getLogger(__name__)

gemini_service = GeminiService()
user_service = UserService()
language_service = LanguageService()


async def _get_image_data(update: Update):
    if update.message.photo:
        photo = update.message.photo[-1]
        photo_file = await photo.get_file()
        image_byte_array = await photo_file.download_as_bytearray()
        return bytes(image_byte_array)
    return None


async def _ban_and_delete(
    update: Update, context: ContextTypes.DEFAULT_TYPE, chat, user, reason: str
):
    logger.warning(f"{reason}. Deleting and Banning.")
    try:
        await update.message.delete()
        await context.bot.ban_chat_member(chat_id=chat.id, user_id=user.id)
        increment_blocked_count()
        logger.info(f"User {user.id} banned.")
    except Exception as e:
        logger.error(f"Failed to delete/ban: {e}")


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
    if chat.type not in ["group", "supergroup"]:
        logger.info("Not a group or supergroup. Returning.")
        return

    try:
        text = update.message.text or update.message.caption
        msg_id = update.message.message_id
        chat_id = update.message.chat.id

        logger.info(f"Processing message {msg_id} in chat {chat_id}")

        image_data = await _get_image_data(update)

        # Logic 1: Language Detection
        is_russian = False
        if text and language_service.is_russian(text):
            is_russian = True

        # Logic 2: Determine if we need to analyze
        should_analyze = False

        if is_russian:
            should_analyze = True
            logger.info("Russian message detected. Analyzing...")
        else:
            # Check message count for non-Russian
            user_record = get_user(user.id, chat.id)
            msg_count = user_record.messages_count if user_record else 0

            logger.info(f"User has sent {msg_count} messages.")

            if msg_count >= 2:
                logger.info("Trusted. Skipping check.")
                increment_message_count(user.id, chat.id)
                return

            logger.info(
                f"User has sent {msg_count} messages (Threshold: 2). Analyzing non-Russian message..."
            )
            should_analyze = True

        if not should_analyze:
            logger.info("Not analyzing. Returning.")
            return

        # Logic 3: Analysis
        scam_score = await gemini_service.analyze_content(text, image_data)
        logger.info(f"Gemini Scam Score: {scam_score}")

        if scam_score > SCAM_THRESHOLD:
            logger.info(f"SCAM DETECTED TEXT: {text}")
            reason = f"Scam detected (Score: {scam_score}) in {'Russian' if is_russian else 'non-Russian'} message"
            await _ban_and_delete(update, context, chat, user, reason)
            return

        # Logic 4: Post-Analysis Actions (if not banned)
        if not is_russian:
            # Safe non-Russian message -> Increment count
            increment_message_count(user.id, chat.id)
            return
        else:
            # Safe Russian message -> Check Age
            logger.info(f"Russian message detected but not scam. Checking user age...")
            is_new = await user_service.is_new_user(user.id, chat.id, context)

            if not is_new:
                logger.info("User is OLD. Allowing Russian message.")
                return

            # User is NEW -> Delete & Warn
            logger.info("User is NEW. Deleting and Warning.")
            try:
                await update.message.reply_text(
                    f"@{user.username or user.first_name} Будь ласка, спілкуйтеся Українською🇺🇦, Англійською🇬🇧 або Івритом🇮🇱!"
                )
                await update.message.delete()
            except Exception as e:
                logger.error(f"Failed to delete/warn: {e}")

    except Exception as e:
        logger.error(f"Error in scam_handler: {e}")
