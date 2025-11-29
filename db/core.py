import logging
from datetime import datetime
from db.models import db, GroupMember

logger = logging.getLogger(__name__)

def init_db():
    """Initializes the database and creates tables if they don't exist."""
    try:
        db.connect()
        db.create_tables([GroupMember])
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
