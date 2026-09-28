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

PATTERN_RU = re.compile(r"[а-яё]+", re.IGNORECASE)
PATTERN_EN = re.compile(r"[a-z]+", re.IGNORECASE)
PATTERN_BE = re.compile(r"[а-яёіў'’]+", re.IGNORECASE)