from config import DATABASE_URL
import logging
from peewee import *
from playhouse.db_url import connect
from datetime import datetime

logger = logging.getLogger(__name__)

if DATABASE_URL:
    logger.info("Using DATABASE_URL for database connection")
    db = connect(DATABASE_URL)
else:
    logger.info("Using local database")
    db = SqliteDatabase("bot_database.db")


class BaseModel(Model):
    class Meta:
        database = db


class GroupMember(BaseModel):
    user_id = BigIntegerField()
    chat_id = BigIntegerField()
    join_date = DateTimeField(null=True)
    is_safe = BooleanField(default=False)
    messages_count = IntegerField(default=0)

    class Meta:
        primary_key = CompositeKey("user_id", "chat_id")


class BotStats(BaseModel):
    key = CharField(primary_key=True)
    value = IntegerField(default=0)
