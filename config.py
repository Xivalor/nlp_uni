import re

TARGET_WORD_LIMIT = 5_000_000
MIN_WORD_LENGTH = 2

DATASET_NAME = "wikimedia/wikipedia"
VERSION = "20231101"

LANGUAGES = {
    "Russian": "ru",
    "Belarussian": "be",
    "English": "en",
}

# Языки, для которых есть словарь лемматизации (simplemma).
# Для белорусского словаря пока нет, там лемматизация отключается.
LEMMA_LANGUAGES = {"ru", "en"}

LEMMA_FILENAME_SUFFIX = "_lemma"

PATTERN_RU = re.compile(r"[а-яё]+", re.IGNORECASE)
PATTERN_EN = re.compile(r"[a-z]+", re.IGNORECASE)
PATTERN_BE = re.compile(r"[а-яёіў'’]+", re.IGNORECASE)

OPERATIONS = {
    "Add word",
    "Edit word",
    "Delete word",
}