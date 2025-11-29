import logging
from lingua import Language, LanguageDetectorBuilder

logger = logging.getLogger(__name__)

class LanguageService:
    def __init__(self):
        # Initialize detector with relevant languages to improve accuracy
        languages = [
            Language.RUSSIAN, 
            Language.UKRAINIAN, 
            Language.ENGLISH, 
            Language.HEBREW,
            Language.BULGARIAN
        ]
        self.detector = LanguageDetectorBuilder.from_languages(*languages).build()

    def is_russian(self, text: str) -> bool:
        """
        Checks if the text is primarily Russian.
        """
        if not text:
            return False
            
        try:
            detected_language = self.detector.detect_language_of(text)
            logger.info(f"Detected language: {detected_language}")
            
            if detected_language == Language.RUSSIAN:
                return True
            if detected_language == Language.BULGARIAN:
                return True
                
            return False
        except Exception as e:
            logger.warning(f"Could not detect language: {e}")
            return False
