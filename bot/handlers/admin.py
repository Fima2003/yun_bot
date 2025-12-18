import logging
import datetime
from telegram import Update
from telegram.ext import ContextTypes
from config import ADMIN_ID
from db.core import add_user

logger = logging.getLogger(__name__)


async def unban_user_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Admin only command to manually add a specific user to a specific chat as SAFE.
    Usage: /unban_user <user_id> <chat_id>
    """
    # 1. Private Chat Check
    if update.effective_chat.type != "private":
        return  # Silently ignore in groups to avoid spam/leaking admin existence

    user = update.effective_user

    # 2. Admin ID Check
    if not ADMIN_ID:
        logger.error("ADMIN_ID not set in config.")
        await update.message.reply_text("Error: Admin ID not configured.")
        return

    # Convert to string for comparison to avoid type issues (env var is str)
    if str(user.id) != str(ADMIN_ID):
        logger.warning(f"Unauthorized access attempt to /unban_user by {user.id}")
        return

    # 3. Parse Attributes
    try:
        args = context.args
        if len(args) != 2:
            await update.message.reply_text("Usage: /unban_user <user_id> <chat_id>")
            return

        target_user_id = int(args[0])
        target_chat_id = int(args[1])

        await context.bot.unbanChatMember(
            chat_id=target_chat_id, user_id=target_user_id, only_if_banned=True
        )
        # 4. Execute Logic
        # We set is_safe=True as implied by "admin adding user manually"
        add_user(
            user_id=target_user_id,
            chat_id=target_chat_id,
            join_date=datetime.datetime.now(datetime.timezone.utc),
            is_safe=True,
        )

        await update.message.reply_text(
            f"✅ User {target_user_id} unbanned from Chat {target_chat_id}, and marked as SAFE."
        )
        logger.info(
            f"Manual unban_user executed by admin {user.id}: User {target_user_id} -> Chat {target_chat_id}"
        )

    except ValueError:
        await update.message.reply_text("Error: IDs must be integers.")
    except Exception as e:
        logger.error(f"Error in unban_user_command: {e}")
        await update.message.reply_text(f"❌ Error: {e}")
