import unittest
import asyncio
from unittest.mock import MagicMock, patch
from bot.services.gemini_service import GeminiService

class TestGeminiService(unittest.TestCase):
    def test_gemini_parsing(self):
        service = GeminiService()
        
        # Mock the model response
        mock_response = MagicMock()
        mock_response.text = '{"scam": 0.8}'
        
        service.model = MagicMock()
        service.model.generate_content.return_value = mock_response
        
        # We need to run async function in sync test
        loop = asyncio.new_event_loop()
        result = loop.run_until_complete(service.analyze_content("test"))
        loop.close()
        
        self.assertEqual(result, 0.8)

    def test_gemini_parsing_markdown(self):
        service = GeminiService()
        
        mock_response = MagicMock()
        mock_response.text = '```json\n{"scam": 0.2}\n```'
        
        service.model = MagicMock()
        service.model.generate_content.return_value = mock_response
        
        loop = asyncio.new_event_loop()
        result = loop.run_until_complete(service.analyze_content("test"))
        loop.close()
        
        self.assertEqual(result, 0.2)

if __name__ == '__main__':
    unittest.main()
