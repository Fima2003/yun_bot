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
            self.model = genai.GenerativeModel("gemini-flash-latest")
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

        content = [prompt]
        if text:
            content.append(f"Message Text: {text}")

        if image_data:
            try:
                image = Image.open(io.BytesIO(image_data))
                content.append(image)
            except Exception as e:
                logger.error(f"Error processing image: {e}")

        # Configure safety settings to allow analyzing potentially harmful content (scams)
        safety_settings = {
            genai.types.HarmCategory.HARM_CATEGORY_HARASSMENT: genai.types.HarmBlockThreshold.BLOCK_NONE,
            genai.types.HarmCategory.HARM_CATEGORY_HATE_SPEECH: genai.types.HarmBlockThreshold.BLOCK_NONE,
            genai.types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: genai.types.HarmBlockThreshold.BLOCK_NONE,
            genai.types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: genai.types.HarmBlockThreshold.BLOCK_NONE,
        }

        try:
            response = self.model.generate_content(
                content, safety_settings=safety_settings
            )

            # Check if the prompt was blocked or if there are no candidates
            if response.prompt_feedback and response.prompt_feedback.block_reason:
                logger.warning(
                    f"Gemini blocked content. Start Reason: {response.prompt_feedback.block_reason}"
                )
                # If blocked, treat as high risk/scam to be safe (or just delete)
                return 1.0

            if not response.candidates:
                logger.warning("Gemini returned no candidates.")
                return 0.0

            if not response.parts:
                logger.warning("Gemini returned no parts.")
                return 0.0

            # Log the raw response for debugging
            logger.info(f"Gemini Raw Response: {response.text}")

            # Clean up response text to ensure it's valid JSON
            response_text = response.text.strip()

            # Find the JSON block
            start_index = response_text.find("{")
            end_index = response_text.rfind("}")

            if start_index != -1 and end_index != -1:
                response_text = response_text[start_index : end_index + 1]

            result = json.loads(response_text)
            return float(result.get("scam", 0.0))
        except Exception as e:
            logger.error(f"Error analyzing content with Gemini: {e}")
            # If we fail to analyze, better to be safe? Or fail open?
            # Default to 0.0 (safe) to avoid false bans on technical errors
            return 0.0
