# This line is first to load environment variables
import logging

# Configure logging immediately, before importing other modules that might log at module level
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

from bot.core import run_bot
from db.core import init_db

if __name__ == "__main__":

    init_db()
    run_bot()
