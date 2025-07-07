import logging
from deep_translator import GoogleTranslator
from typing import Optional, Dict
from functools import lru_cache

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)

class FrenchTranslator:
    def __init__(self, source_lang: str = 'en', target_lang: str = 'fr'):
        self.source_lang = source_lang
        self.target_lang = target_lang
        self.translator = self._create_translator()
        self.language_code_map = self._create_language_code_map()

    def _create_translator(self) -> GoogleTranslator:
        return GoogleTranslator(source=self.source_lang, target=self.target_lang)

    @lru_cache(maxsize=1000)
    def translate(self, text: str) -> str:
        if not text:
            return text

        try:
            return self.translator.translate(text)
        except Exception as e:
            logger.error(f"Translation error: {e}")
            return text

    def change_source_language(self, new_source_lang: str) -> None:
        supported_languages = self.get_supported_languages()
        if supported_languages is None:
            raise ValueError("Unable to fetch supported languages")
        
        new_source_lang = new_source_lang.lower()
        if new_source_lang in self.language_code_map:
            new_source_lang = self.language_code_map[new_source_lang]
        
        if new_source_lang not in supported_languages:
            raise ValueError(f"Unsupported language: {new_source_lang}")
        
        self.source_lang = new_source_lang
        self.translator = self._create_translator()
        self.translate.cache_clear()

    @lru_cache(maxsize=1)
    def get_supported_languages(self) -> Optional[Dict[str, str]]:
        try:
            return self.translator.get_supported_languages(as_dict=True)
        except Exception as e:
            logger.error(f"Error fetching supported languages: {e}")
            return None

    def batch_translate(self, texts: list[str]) -> list[str]:
        return [self.translate(text) for text in texts]

    def _create_language_code_map(self) -> Dict[str, str]:
        return {
            'en': 'english',
            'fr': 'french',
            # 'es': 'spanish',
            # 'de': 'german',
            # 'it': 'italian',
            # 'pt': 'portuguese',
            # 'ru': 'russian',
            # 'ja': 'japanese',
            # 'ko': 'korean',
            # 'zh': 'chinese (simplified)'
        }