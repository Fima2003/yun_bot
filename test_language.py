import unittest
from bot.services.language_service import LanguageService

class TestLanguageService(unittest.TestCase):
    def test_is_russian(self):
        service = LanguageService()
        
        # Russian text
        self.assertTrue(service.is_russian("Привет, это тестовое сообщение на русском языке."))
        self.assertTrue(service.is_russian("Это русский текст."))
        
        # Ukrainian text
        self.assertFalse(service.is_russian("Привіт, як справи?"))
        self.assertFalse(service.is_russian("Це український текст."))
        
        # English text
        self.assertFalse(service.is_russian("Hello, how are you?"))
        
        # Mixed/Ambiguous (should default to False or whatever langdetect says, usually robust)
        self.assertFalse(service.is_russian("12345")) # Numbers usually not detected as RU

if __name__ == '__main__':
    unittest.main()
