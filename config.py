import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")
SCAM_THRESHOLD = 0.75
NEW_USER_THRESHOLD_DAYS = 2

# Startup Cleanup Variables
CLEANUP_CHAT_ID = os.getenv("CLEANUP_CHAT_ID")
CLEANUP_MESSAGE_ID = os.getenv("CLEANUP_MESSAGE_ID")
CLEANUP_USER_ID = os.getenv("CLEANUP_USER_ID")
ADMIN_ID = os.getenv("ADMIN_ID")
