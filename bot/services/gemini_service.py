import logging
import json
import io
from PIL import Image
import google.generativeai as genai
from config import GEMINI_API_KEY

logger = logging.getLogger(__name__)

class GeminiService:
    def __init__(self):
        if GEMINI_API_KEY:
            genai.configure(api_key=GEMINI_API_KEY)
            self.model = genai.GenerativeModel('gemini-flash-latest')
        else:
            logger.error("GEMINI_API_KEY not found in environment variables.")
            self.model = None

    async def analyze_content(self, text: str, image_data: bytes = None) -> float:
        """
        Analyzes text and optional image using Gemini to determine scam probability.
        Returns a float between 0.0 and 1.0.
        """
        if not self.model:
            logger.error("Gemini model not initialized.")
            return 0.0

        prompt = """
        You are a scam detection expert. Analyze the following message (and image if provided) to determine if it is a scam, fraud, or spam.
        
        Return your answer strictly in this JSON format:
        {
            "scam": <double between 0.0 and 1.0>
        }
        
        "scam" indicates the possibility of this message being a scam. 
        0.0 means definitely safe.
        1.0 means definitely a scam.
        
        Consider:
        - Crypto giveaways
        - Phishing links
        - "You won a prize" messages
        - Urgent requests for money
        - Suspicious investment opportunities
        """
        
        content = [prompt]
        if text:
            content.append(f"Message Text: {text}")
        
        if image_data:
            try:
                image = Image.open(io.BytesIO(image_data))
                content.append(image)
            except Exception as e:
                logger.error(f"Error processing image: {e}")

        try:
            response = self.model.generate_content(content)
            # Clean up response text to ensure it's valid JSON
            response_text = response.text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:-3].strip()
            elif response_text.startswith("```"):
                response_text = response_text[3:-3].strip()
                
            result = json.loads(response_text)
            return float(result.get("scam", 0.0))
        except Exception as e:
            logger.error(f"Error analyzing content with Gemini: {e}")
            return 0.0
