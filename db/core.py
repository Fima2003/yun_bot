import logging
import json
from datetime import datetime
from datetime import datetime
from db.models import db, GroupMember, BotStats, Chat

logger = logging.getLogger(__name__)


from peewee import fn


import json

# ...


def update_excluded_threads(chat_id: int, thread_ids: list[int]):
    """Updates the list of excluded threads for a chat."""
    try:
        chat, created = Chat.get_or_create(chat_id=chat_id)

        try:
            current_threads = json.loads(chat.threads_to_exclude)
        except json.JSONDecodeError:
            current_threads = []

        # Use set for uniqueness then convert back to list
        updated_threads = list(set(current_threads + thread_ids))

        chat.threads_to_exclude = json.dumps(updated_threads)
        chat.save()
        logger.info(f"Updated excluded threads for Chat {chat_id}: {updated_threads}")
        return True
    except Exception as e:
        logger.error(f"Error updating excluded threads: {e}")
        return True
    except Exception as e:
        logger.error(f"Error updating excluded threads: {e}")
        return False


def get_excluded_threads(chat_id: int) -> list[int]:
    """Retrieves the list of excluded threads for a chat."""
    try:
        chat = Chat.get_or_none(Chat.chat_id == chat_id)
        if chat and chat.threads_to_exclude:
            return json.loads(chat.threads_to_exclude)
        return []
    except Exception as e:
        logger.error(f"Error getting excluded threads: {e}")
        return []


def migrate_chats():
    """Migrates existing GroupMembers to populates the Chat table."""
    try:
        # Group members by chat_id and count them
        query = GroupMember.select(
            GroupMember.chat_id, fn.COUNT(GroupMember.user_id).alias("member_count")
        ).group_by(GroupMember.chat_id)

        for entry in query:
            chat_id = entry.chat_id
            count = entry.member_count

            # Create or get the Chat record
            chat, created = Chat.get_or_create(chat_id=chat_id)

            # Update known_users
            if chat.known_users != count:
                chat.known_users = count
                chat.save()
                logger.info(f"Migrated Chat {chat_id}: Updated known_users to {count}")
            elif created:
                chat.known_users = count
                chat.save()
                logger.info(
                    f"Migrated Chat {chat_id}: Created with {count} known_users"
                )

        logger.info("Chat table migration completed.")
    except Exception as e:
        logger.error(f"Error migrating chats: {e}")


def init_db():
    """Initializes the database and creates tables if they don't exist."""
    try:
        db.connect()
        # User commented out drop_tables to preserve data for migration
        # db.drop_tables([GroupMember, BotStats, Chat], safe=True)
        db.create_tables([GroupMember, BotStats, Chat])

        # Run migration to populate Chat table from existing GroupMembers
        migrate_chats()

        logger.info("Database initialized successfully.")
        db.close()
    except Exception as e:
        logger.error(f"Error initializing database: {e}")


def add_user(
    user_id: int, chat_id: int, join_date: datetime = None, is_safe: bool = False
):
    """Adds or updates a user in the database. Returns True if successful."""
    try:
        user = GroupMember.get_or_none(
            (GroupMember.user_id == user_id) & (GroupMember.chat_id == chat_id)
        )

        if user:
            # User exists
            if is_safe:
                # If is_safe is True, enforce overwrite (as requested)
                user.is_safe = True
                user.join_date = join_date
                user.save()
                logger.info(
                    f"User {user_id} in {chat_id} overwritten with is_safe=True"
                )
        else:
            # User does not exist
            GroupMember.create(
                user_id=user_id, chat_id=chat_id, join_date=join_date, is_safe=is_safe
            )
        return True
    except Exception as e:
        logger.error(f"Error adding user to DB: {e}")
        return False


def get_user(user_id: int, chat_id: int):
    """Retrieves a user from the database."""
    try:
        return GroupMember.get(
            (GroupMember.user_id == user_id) & (GroupMember.chat_id == chat_id)
        )
    except GroupMember.DoesNotExist:
        return None
    except Exception as e:
        logger.error(f"Error getting user from DB: {e}")
        return None


def set_user_safe(user_id: int, chat_id: int, is_safe: bool = True):
    """Updates the is_safe flag for a user."""
    try:
        query = GroupMember.update(is_safe=is_safe).where(
            (GroupMember.user_id == user_id) & (GroupMember.chat_id == chat_id)
        )
        query.execute()
    except Exception as e:
        logger.error(f"Error setting user safe in DB: {e}")


def increment_message_count(user_id: int, chat_id: int):
    """Increments the message count for a user, creating them if they don't exist."""
    try:
        user, created = GroupMember.get_or_create(
            user_id=user_id,
            chat_id=chat_id,
            defaults={
                "messages_count": 1,
                "join_date": datetime.now(),  # Using standard datetime
            },
        )
        if not created:
            user.messages_count += 1
            user.save()
    except Exception as e:
        logger.error(f"Error incrementing message count: {e}")


def increment_blocked_count(chat_id: int = None):
    """Increments the global counter of blocked bots and optionally updates chat-specific banned count."""
    try:
        # 1. Global Stats
        stat, created = BotStats.get_or_create(
            key="blocked_bots", defaults={"value": 0}
        )
        BotStats.update(value=BotStats.value + 1).where(
            BotStats.key == "blocked_bots"
        ).execute()

        # 2. Chat Stats
        if chat_id:
            chat, created_chat = Chat.get_or_create(chat_id=chat_id)
            # We use an atomic update here too where possible, or just increment
            Chat.update(banned_users=Chat.banned_users + 1).where(
                Chat.chat_id == chat_id
            ).execute()

    except Exception as e:
        logger.error(f"Error incrementing blocked count: {e}")


def get_blocked_count() -> int:
    """Returns the total number of blocked bots."""
    try:
        stat = BotStats.get_or_none(BotStats.key == "blocked_bots")
        return stat.value if stat else 0
    except Exception as e:
        logger.error(f"Error getting blocked count: {e}")
        return 0
