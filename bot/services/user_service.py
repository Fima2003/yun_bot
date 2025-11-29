from datetime import datetime, timezone
import logging
from telegram.ext import ContextTypes
from telegram.constants import ChatMemberStatus
from config import NEW_USER_THRESHOLD_DAYS
from db.core import get_user, add_user, set_user_safe

logger = logging.getLogger(__name__)

class UserService:
    async def is_new_user(self, user_id: int, chat_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
        """
        Checks if the user is considered 'new' based on DB records.
        Returns True if new (needs checking), False if safe.
        """
        try:
            # Check DB
            user_record = get_user(user_id, chat_id)
            
            if not user_record:
                # Case A: User NOT in DB -> Old User (Safe)
                logger.info(f"User {user_id} not in DB. Marking as safe (Old User).")
                add_user(user_id, chat_id, join_date=None, is_safe=True)
                return False
            
            # Case B: User IN DB
            if user_record.is_safe:
                return False
                
            join_date = user_record.join_date
            if not join_date:
                # Should not happen if is_safe is False, but handle gracefully
                return False

            # Peewee might return string if SQLite storage was raw
            if isinstance(join_date, str):
                try:
                    join_date = datetime.fromisoformat(join_date)
                except ValueError:
                    # Fallback for formats like "2025-11-29 12:00:00"
                    join_date = datetime.strptime(join_date.split('.')[0], "%Y-%m-%d %H:%M:%S")
            
            # Ensure join_date is timezone aware
            if join_date.tzinfo is None:
                join_date = join_date.replace(tzinfo=timezone.utc)

            now = datetime.now(timezone.utc)
            time_diff = now - join_date
            
            if time_diff.days > NEW_USER_THRESHOLD_DAYS:
                # User has been here long enough -> Mark safe
                logger.info(f"User {user_id} passed threshold ({time_diff.days} days). Marking safe.")
                set_user_safe(user_id, chat_id, True)
                return False
            
            # User is still new
            logger.info(f"User {user_id} is new ({time_diff.days} days).")
            return True

        except Exception as e:
            logger.error(f"Error checking user status: {e}", exc_info=True)
            # Fail safe: assume safe to avoid spamming errors? Or assume new?
            # Let's assume safe to avoid blocking legitimate users on error.
            return False
