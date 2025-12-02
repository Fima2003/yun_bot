import logging
from datetime import datetime
from db.models import db, GroupMember, BotStats

logger = logging.getLogger(__name__)

def init_db():
    """Initializes the database and creates tables if they don't exist."""
    try:
        db.connect()
        db.create_tables([GroupMember, BotStats])
        logger.info("Database initialized successfully.")
        db.close()
    except Exception as e:
        logger.error(f"Error initializing database: {e}")

def add_user(user_id: int, chat_id: int, join_date: datetime = None, is_safe: bool = False):
    """Adds or updates a user in the database."""
    try:
        # Peewee's insert_or_replace equivalent usually involves checking existence or using specific dialect features.
        # For SQLite, replace() works.
        GroupMember.create(
            user_id=user_id,
            chat_id=chat_id,
            join_date=join_date,
            is_safe=is_safe
        )
    except Exception as e:
        logger.error(f"Error adding user to DB: {e}")

def get_user(user_id: int, chat_id: int):
    """Retrieves a user from the database."""
    try:
        return GroupMember.get((GroupMember.user_id == user_id) & (GroupMember.chat_id == chat_id))
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
    """Increments the message count for a user."""
    try:
        query = GroupMember.update(messages_count=GroupMember.messages_count + 1).where(
            (GroupMember.user_id == user_id) & (GroupMember.chat_id == chat_id)
        )
        query.execute()
    except Exception as e:
        logger.error(f"Error incrementing message count: {e}")

def increment_blocked_count():
    """Increments the global counter of blocked bots."""
    try:
        # Atomic update using Peewee's expressions
        # upsert: try to insert 1, on conflict update value = value + 1
        # SQLite replace/insert is tricky, but Postgres supports ON CONFLICT.
        # For simplicity and cross-db compatibility (mostly), we can try get_or_create then update.
        stat, created = BotStats.get_or_create(key='blocked_bots', defaults={'value': 0})
        BotStats.update(value=BotStats.value + 1).where(BotStats.key == 'blocked_bots').execute()
    except Exception as e:
        logger.error(f"Error incrementing blocked count: {e}")

def get_blocked_count() -> int:
    """Returns the total number of blocked bots."""
    try:
        stat = BotStats.get_or_none(BotStats.key == 'blocked_bots')
        return stat.value if stat else 0
    except Exception as e:
        logger.error(f"Error getting blocked count: {e}")
        return 0
