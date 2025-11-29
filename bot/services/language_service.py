import logging
from langdetect import detect, LangDetectException, DetectorFactory

DetectorFactory.seed = 0

logger = logging.getLogger(__name__)

class LanguageService:
    def is_russian(self, text: str) -> bool:
        """
        Detects if the text is Russian.
        Returns True if Russian, False otherwise.
        """
        if not text:
            return False
            
        try:
            lang = detect(text)
            logger.info(f"Detected language: {lang}")
            return lang == 'ru'
        except LangDetectException as e:
            logger.warning(f"Could not detect language: {e}")
            return False
        except Exception as e:
            logger.error(f"Error in language detection: {e}")
            return False
