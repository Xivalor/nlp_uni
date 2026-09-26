import re

# Лимиты для токенизатора
TARGET_WORD_LIMIT = 5_000_000
MIN_WORD_LENGTH = 2

# Конфигурация датасета
WIKIPEDIA_DATASET_NAME = "wikipedia"
WIKIPEDIA_VERSION = "20220301"

# Паттерны регулярных выражений (компилируем один раз прямо в конфиге)
PATTERN_RU = re.compile(r"[а-яё]+", re.IGNORECASE)
PATTERN_EN = re.compile(r"[a-z]+", re.IGNORECASE)
PATTERN_BE = re.compile(r"[а-яёіў'’]+", re.IGNORECASE)