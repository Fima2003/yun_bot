from peewee import *
from playhouse.db_url import connect
from datetime import datetime
import os

# Check for DATABASE_URL environment variable (common in PaaS like Railway)
database_url = os.getenv("DATABASE_URL")

if database_url:
    db = connect(database_url)
else:
    db = SqliteDatabase('bot_database.db')

class BaseModel(Model):
    class Meta:
        database = db

class GroupMember(BaseModel):
    user_id = IntegerField()
    chat_id = IntegerField()
    join_date = DateTimeField(null=True)
    is_safe = BooleanField(default=False)

    class Meta:
        primary_key = CompositeKey('user_id', 'chat_id')
