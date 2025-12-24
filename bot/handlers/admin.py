import logging
import datetime
from telegram import Update
from telegram.ext import ContextTypes
from config import ADMIN_ID
from db.core import add_user, increment_blocked_count, update_excluded_threads

# ... existing code ...


async def remove_thread_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Admin only command to exclude specific threads from scam checking in a chat.
    Usage: /remove_thread <thread_ids_comma_sep> <chat_id>
    Example: /remove_thread 12,34 100123456
    """
    # 1. Private Chat Check
    if update.effective_chat.type != "private":
        return

    user = update.effective_user

    # 2. Admin ID Check
    if not ADMIN_ID or str(user.id) != str(ADMIN_ID):
        logger.warning(f"Unauthorized access attempt to /remove_thread by {user.id}")
        return

    # 3. Parse Attributes
    try:
        args = context.args
        if len(args) != 2:
            await update.message.reply_text(
                "Usage: /remove_thread <thread_ids> <chat_id>\nExample: /remove_thread 12,34 -100123456"
            )
            return

        thread_ids_str = args[0]
        target_chat_id = int(args[1])

        # Parse thread IDs
        try:
            thread_ids = [
                int(tid.strip()) for tid in thread_ids_str.split(",") if tid.strip()
            ]
        except ValueError:
            await update.message.reply_text(
                "Error: Thread IDs must be integers separated by commas."
            )
            return

        # 4. Execute Logic
        success = update_excluded_threads(chat_id=target_chat_id, thread_ids=thread_ids)

        if success:
            await update.message.reply_text(
                f"✅ Excluded threads {thread_ids} for Chat {target_chat_id}"
            )
            logger.info(
                f"Admin {user.id} excluded threads {thread_ids} in {target_chat_id}"
            )
        else:
            await update.message.reply_text("❌ Error updating database.")

    except ValueError:
        await update.message.reply_text("Error: Chat ID must be an integer.")
    except Exception as e:
        logger.error(f"Error in remove_thread_command: {e}")
        await update.message.reply_text(f"❌ Error: {e}")


logger = logging.getLogger(__name__)


async def unban_user_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Admin only command to manually unban a user and mark them as SAFE in DB.
    Usage: /unban_user <user_id> <chat_id>
    """
    # 1. Private Chat Check
    if update.effective_chat.type != "private":
        return

    user = update.effective_user

    # 2. Admin ID Check
    if not ADMIN_ID or str(user.id) != str(ADMIN_ID):
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

        # 4. Telegram Action: Unban
        try:
            success = await context.bot.unban_chat_member(
                chat_id=target_chat_id, user_id=target_user_id, only_if_banned=True
            )
            msg_action = (
                "unbanned from" if success else "processed (unban skipped/failed) for"
            )
        except Exception as e:
            logger.warning(
                f"Unban failed for {target_user_id} in {target_chat_id}: {e}"
            )
            msg_action = "processed (unban skipped/failed) for"

        # 5. DB Action: Mark Safe
        add_user(
            user_id=target_user_id,
            chat_id=target_chat_id,
            join_date=datetime.datetime.now(datetime.timezone.utc),
            is_safe=True,
        )

        await update.message.reply_text(
            f"✅ User {target_user_id} {msg_action} Chat {target_chat_id}, and marked as SAFE."
        )
        logger.info(
            f"Manual unban_user executed by admin {user.id}: User {target_user_id} -> Chat {target_chat_id}"
        )

    except ValueError:
        await update.message.reply_text("Error: IDs must be integers.")
    except Exception as e:
        logger.error(f"Error in unban_user_command: {e}")
        await update.message.reply_text(f"❌ Error: {e}")


async def ban_user_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Admin only command to manually ban a user and mark them as UNSAFE in DB.
    Usage: /ban_user <user_id> <chat_id>
    """
    # 1. Private Chat Check
    if update.effective_chat.type != "private":
        return

    user = update.effective_user

    # 2. Admin ID Check
    if not ADMIN_ID or str(user.id) != str(ADMIN_ID):
        logger.warning(f"Unauthorized access attempt to /ban_user by {user.id}")
        return

    # 3. Parse Attributes
    try:
        args = context.args
        if len(args) != 2:
            await update.message.reply_text("Usage: /ban_user <user_id> <chat_id>")
            return

        target_user_id = int(args[0])
        target_chat_id = int(args[1])

        # 4. Telegram Action: Ban
        try:
            await context.bot.ban_chat_member(
                chat_id=target_chat_id, user_id=target_user_id
            )
            msg_action = "banned from"
        except Exception as e:
            logger.warning(f"Ban failed for {target_user_id} in {target_chat_id}: {e}")
            msg_action = "processed (ban failed) for"

        # 5. DB Action: Mark Unsafe
        add_user(
            user_id=target_user_id,
            chat_id=target_chat_id,
            join_date=datetime.datetime.now(datetime.timezone.utc),
            is_safe=False,
        )

        # 6. Update Stats
        increment_blocked_count(chat_id=target_chat_id)

        await update.message.reply_text(
            f"🚫 User {target_user_id} {msg_action} Chat {target_chat_id}, and marked as UNSAFE."
        )
        logger.info(
            f"Manual ban_user executed by admin {user.id}: User {target_user_id} -> Chat {target_chat_id}"
        )

    except ValueError:
        await update.message.reply_text("Error: IDs must be integers.")
    except Exception as e:
        logger.error(f"Error in ban_user_command: {e}")
        await update.message.reply_text(f"❌ Error: {e}")
