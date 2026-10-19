"""Лемматизация: приведение словоформы к нормальной форме (лемме)."""

from config import LEMMA_LANGUAGES


class Lemmatizer():

    def __init__(self, lang_code, enabled=True):
        self.lang_code = lang_code
        self.enabled = enabled and lang_code in LEMMA_LANGUAGES

        self._engine = None
        if self.enabled:
            try:
                import simplemma
                self._engine = simplemma.lemmatize
            except ImportError:
                self.enabled = False


    def lemmatize(self, word: str) -> str:
        """Возвращает лемму для слова. Если лемматизация недоступна — само слово."""
        if not self.enabled:
            return word
        return self._engine(word, lang=self.lang_code)


    def lemmatize_query(self, query: str) -> str:
        """Лемматизирует запрос поиска: каждое отдельное слово запроса."""
        if not self.enabled:
            return query
        return ' '.join(self.lemmatize(word) for word in query.split())
