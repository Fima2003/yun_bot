# This line is first to load environment variables
import config
import logging

# Configure logging immediately, before importing other modules that might log at module level
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

from bot.core import run_bot
from db.core import init_db
from db.models import db, GroupMember

if __name__ == '__main__':
    # FORCE RESET: Drop the table to ensure it's recreated with BigInteger
    try:
        db.connect()
        db.drop_tables([GroupMember])
        db.close()
        logging.info("Table dropped successfully.")
    except Exception as e:
        logging.error(f"Error dropping table: {e}")

    init_db()
    run_bot()
