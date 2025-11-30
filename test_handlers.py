import unittest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from bot.handlers.scam_handler import scam_handler
from config import SCAM_THRESHOLD

class TestHandlers(unittest.TestCase):
    def test_scam_handler_bans_user(self):
        # Mock Update and Context
        update = MagicMock()
        update.message.from_user.id = 123
        update.message.chat.id = 456
        update.message.chat.type = 'group'
        update.message.text = "Free crypto!"
        update.message.photo = []
        
        context = MagicMock()
        context.bot.get_file = AsyncMock()
        context.bot.ban_chat_member = AsyncMock()
        update.message.delete = AsyncMock()

        # Mock Services
        with patch('bot.handlers.user_service') as mock_user_service, \
             patch('bot.handlers.gemini_service') as mock_gemini_service:
            
            # User is new
            mock_user_service.is_new_user = AsyncMock(return_value=True)
            
            # Content is scam
            mock_gemini_service.analyze_content = AsyncMock(return_value=0.9) # > 0.75

            # Run handler
            loop = asyncio.new_event_loop()
            loop.run_until_complete(scam_handler(update, context))
            loop.close()

            # Verify delete and ban were called
            update.message.delete.assert_called_once()
            context.bot.ban_chat_member.assert_called_once_with(456, 123)

    def test_scam_handler_no_ban_safe_message(self):
        # Mock Update and Context
        update = MagicMock()
        update.message.from_user.id = 123
        update.message.chat.id = 456
        update.message.chat.type = 'group'
        update.message.text = "Hello world"
        update.message.photo = []
        
        context = MagicMock()
        context.bot.ban_chat_member = AsyncMock()
        update.message.delete = AsyncMock()

        # Mock Services
        with patch('bot.handlers.user_service') as mock_user_service, \
             patch('bot.handlers.gemini_service') as mock_gemini_service:
            
            # User is new
            mock_user_service.is_new_user = AsyncMock(return_value=True)
            
            # Content is safe
            mock_gemini_service.analyze_content = AsyncMock(return_value=0.1)

            # Run handler
            loop = asyncio.new_event_loop()
            loop.run_until_complete(scam_handler(update, context))
            loop.close()

            # Verify delete and ban were NOT called
            update.message.delete.assert_not_called()
            context.bot.ban_chat_member.assert_not_called()

    def test_scam_handler_russian_message(self):
        # Mock Update and Context
        update = MagicMock()
        update.message.from_user.id = 123
        update.message.chat.id = 456
        update.message.chat.type = 'group'
        update.message.text = "Привет" # Russian
        update.message.photo = []
        
        context = MagicMock()
        update.message.delete = AsyncMock()

        # Mock Services
        with patch('bot.handlers.user_service') as mock_user_service, \
             patch('bot.handlers.gemini_service') as mock_gemini_service, \
             patch('bot.handlers.language_service') as mock_language_service:
            
            # User is new
            mock_user_service.is_new_user = AsyncMock(return_value=True)
            
            # Language is Russian
            mock_language_service.is_russian.return_value = True

            # Run handler
            loop = asyncio.new_event_loop()
            loop.run_until_complete(scam_handler(update, context))
            loop.close()

            # Verify delete called, but NO ban (as per current logic)
            update.message.delete.assert_called_once()
            # Gemini should NOT be called
            mock_gemini_service.analyze_content.assert_not_called()

    def test_scam_handler_non_russian(self):
        # Setup
        update = MagicMock()
        update.message.from_user.id = 123
        update.message.chat.id = 456
        update.message.chat.type = 'group'
        update.message.text = "Hello world"
        update.message.photo = []
        context = MagicMock()
        context.bot.ban_chat_member = AsyncMock()
        update.message.delete = AsyncMock()
        update.message.reply_text = AsyncMock() # For potential replies

        # Mock services
        with patch('bot.handlers.user_service') as mock_user_service, \
             patch('bot.handlers.gemini_service') as mock_gemini_service, \
             patch('bot.handlers.language_service') as mock_language_service:
            
            # Language: Not Russian
            mock_language_service.is_russian.return_value = False
            
            # Run handler
            loop = asyncio.new_event_loop()
            from bot.handlers.scam_handler import handle_scam
            loop.run_until_complete(handle_scam(update, context))
            loop.close()
            
            # Assertions
            # Should check language
            mock_language_service.is_russian.assert_called_once()
            # Should NOT check Gemini
            mock_gemini_service.analyze_content.assert_not_called()
            # Should NOT check user age
            mock_user_service.is_new_user.assert_not_called()
            # Should not delete or ban
            update.message.delete.assert_not_called()
            context.bot.ban_chat_member.assert_not_called()
            update.message.reply_text.assert_not_called()

    def test_scam_handler_russian_scam(self):
        # Setup
        update = MagicMock()
        update.message.from_user.id = 123
        update.message.chat.id = 456
        update.message.chat.type = 'group'
        update.message.text = "Привет, это скам"
        update.message.photo = []
        context = MagicMock()
        context.bot.ban_chat_member = AsyncMock()
        update.message.delete = AsyncMock()
        update.message.reply_text = AsyncMock() # For potential replies
        
        # Mock services
        with patch('bot.handlers.user_service') as mock_user_service, \
             patch('bot.handlers.gemini_service') as mock_gemini_service, \
             patch('bot.handlers.language_service') as mock_language_service:
            
            mock_language_service.is_russian.return_value = True
            mock_gemini_service.analyze_content = AsyncMock(return_value=0.9) # High scam score
            
            # Run handler
            loop = asyncio.new_event_loop()
            from bot.handlers.scam_handler import handle_scam
            loop.run_until_complete(handle_scam(update, context))
            loop.close()
            
            # Assertions
            # Should check language
            mock_language_service.is_russian.assert_called_once()
            # Should check Gemini
            mock_gemini_service.analyze_content.assert_called_once()
            # Should delete and ban
            update.message.delete.assert_called_once()
            context.bot.ban_chat_member.assert_called_once_with(456, 123)
            # Should not check user age or reply
            mock_user_service.is_new_user.assert_not_called()
            update.message.reply_text.assert_not_called()

    def test_scam_handler_russian_not_scam_old_user(self):
        # Setup
        update = MagicMock()
        update.message.from_user.id = 123
        update.message.chat.id = 456
        update.message.chat.type = 'group'
        update.message.text = "Привет, я старый юзер"
        update.message.photo = []
        context = MagicMock()
        context.bot.ban_chat_member = AsyncMock()
        update.message.delete = AsyncMock()
        update.message.reply_text = AsyncMock() # For potential replies
        
        # Mock services
        with patch('bot.handlers.user_service') as mock_user_service, \
             patch('bot.handlers.gemini_service') as mock_gemini_service, \
             patch('bot.handlers.language_service') as mock_language_service:
            
            mock_language_service.is_russian.return_value = True
            mock_gemini_service.analyze_content = AsyncMock(return_value=0.1) # Low scam score
            mock_user_service.is_new_user = AsyncMock(return_value=False) # Old user
            
            # Run handler
            loop = asyncio.new_event_loop()
            from bot.handlers.scam_handler import handle_scam
            loop.run_until_complete(handle_scam(update, context))
            loop.close()
            
            # Assertions
            # Should check language, Gemini, and User Age
            mock_language_service.is_russian.assert_called_once()
            mock_gemini_service.analyze_content.assert_called_once()
            mock_user_service.is_new_user.assert_called_once()
            # Should NOT delete or ban or reply
            update.message.delete.assert_not_called()
            context.bot.ban_chat_member.assert_not_called()
            update.message.reply_text.assert_not_called()

    def test_scam_handler_russian_not_scam_new_user(self):
        # Setup
        update = MagicMock()
        update.message.from_user.id = 123
        update.message.chat.id = 456
        update.message.chat.type = 'group'
        update.message.text = "Привет, я новый юзер"
        update.message.photo = []
        context = MagicMock()
        context.bot.ban_chat_member = AsyncMock()
        update.message.delete = AsyncMock()
        update.message.reply_text = AsyncMock() # For potential replies
        
        # Mock services
        with patch('bot.handlers.user_service') as mock_user_service, \
             patch('bot.handlers.gemini_service') as mock_gemini_service, \
             patch('bot.handlers.language_service') as mock_language_service:
            
            mock_language_service.is_russian.return_value = True
            mock_gemini_service.analyze_content = AsyncMock(return_value=0.1) # Low scam score
            mock_user_service.is_new_user = AsyncMock(return_value=True) # New user
            
            # Run handler
            loop = asyncio.new_event_loop()
            from bot.handlers.scam_handler import handle_scam
            loop.run_until_complete(handle_scam(update, context))
            loop.close()
            
            # Assertions
            # Should check language, Gemini, and User Age
            mock_language_service.is_russian.assert_called_once()
            mock_gemini_service.analyze_content.assert_called_once()
            mock_user_service.is_new_user.assert_called_once()
            # Should delete and warn (reply)
            update.message.delete.assert_called_once()
            update.message.reply_text.assert_called_once()
            context.bot.ban_chat_member.assert_not_called()

    def test_start_command(self):
        update = MagicMock()
        update.message.reply_text = AsyncMock()
        context = MagicMock()

        loop = asyncio.new_event_loop()
        # We need to import start_command inside the test or at top level if not already imported
        from bot.handlers import start_command
        loop.run_until_complete(start_command(update, context))
        loop.close()

        update.message.reply_text.assert_called_once_with("Вітаю, Юначе!")

if __name__ == '__main__':
    unittest.main()
```
