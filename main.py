# This line is first to load environment variables
import config
import logging
from bot.core import run_bot
from db.core import init_db
# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

if __name__ == '__main__':
    init_db()
    run_bot()
