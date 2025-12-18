import logging
import json
import io
from PIL import Image
from google import genai
from google.genai import types
from config import GEMINI_API_KEY

logger = logging.getLogger(__name__)


class GeminiService:
    def __init__(self):
        if GEMINI_API_KEY:
            self.client = genai.Client(api_key=GEMINI_API_KEY)
            self.model_name = "gemini-flash-latest"
        else:
            logger.error("GEMINI_API_KEY not found in environment variables.")
            self.client = None
            self.model_name = None

    async def analyze_content(self, text: str, image_data: bytes = None) -> float:
        """
        Analyzes text and optional image using Gemini to determine scam probability.
        Returns a float between 0.0 and 1.0.
        """
        if not self.client:
            logger.error("Gemini client not initialized.")
            return 0.0

        prompt = """
        You are a scam detection expert. Analyze the following message (and image if provided) to determine if it is a scam, fraud, or spam.
        
        Return your answer strictly in this JSON format:
        {
            "scam": <double between 0.0 and 1.0>
        }
        
        Do NOT return any other text, markdown formatting, or explanations. Return ONLY the JSON object.
        
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

        contents = []
        if text:
            # Combine prompt and text into one string or use multiple parts.
            # Using single string for clarity in prompt structure.
            full_prompt = f"{prompt}\n\nMessage Text: {text}"
            contents.append(full_prompt)
        else:
            contents.append(prompt)

        if image_data:
            try:
                # google-genai SDK handles PIL images
                image = Image.open(io.BytesIO(image_data))
                contents.append(image)
            except Exception as e:
                logger.error(f"Error processing image: {e}")

        # Configure safety settings
        safety_settings = [
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_HARASSMENT,
                threshold=types.HarmBlockThreshold.BLOCK_NONE,
            ),
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                threshold=types.HarmBlockThreshold.BLOCK_NONE,
            ),
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                threshold=types.HarmBlockThreshold.BLOCK_NONE,
            ),
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                threshold=types.HarmBlockThreshold.BLOCK_NONE,
            ),
        ]

        config = types.GenerateContentConfig(safety_settings=safety_settings)

        try:
            # Use client.aio for async calls
            response = await self.client.aio.models.generate_content(
                model=self.model_name, contents=contents, config=config
            )

            if not response.text:
                logger.warning("Gemini returned no text.")
                return 0.0

            logger.info(f"Gemini Raw Response: {response.text}")

            response_text = response.text.strip()

            # Robust JSON extraction
            start_index = response_text.find("{")
            end_index = response_text.rfind("}")

            if start_index != -1 and end_index != -1:
                response_text = response_text[start_index : end_index + 1]

            result = json.loads(response_text)
            return float(result.get("scam", 0.0))

        except Exception as e:
            logger.error(f"Error analyzing content with Gemini: {e}")
            return 0.0
