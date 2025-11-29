import unittest
import os
from datetime import datetime, timezone
from db.core import init_db, add_user, get_user, set_user_safe
from db.models import db

class TestDB(unittest.TestCase):
    def setUp(self):
        # Use a test DB
        self.test_db = "test_bot_database.db"
        
        # Configure Peewee to use test DB
        db.init(self.test_db)
        
        init_db()

    def tearDown(self):
        db.close()
        if os.path.exists(self.test_db):
            os.remove(self.test_db)

    def test_add_get_user(self):
        now = datetime.now(timezone.utc)
        add_user(1, 100, now, False)
        
        user = get_user(1, 100)
        self.assertIsNotNone(user)
        self.assertEqual(user.user_id, 1)
        self.assertEqual(user.chat_id, 100)
        self.assertEqual(user.is_safe, False)

    def test_set_user_safe(self):
        now = datetime.now(timezone.utc)
        add_user(2, 100, now, False)
        
        set_user_safe(2, 100, True)
        user = get_user(2, 100)
        self.assertEqual(user.is_safe, True)

if __name__ == '__main__':
    unittest.main()
