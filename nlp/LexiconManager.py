import re
import os
import json
from datasets import load_dataset
from collections import Counter
from config import WIKIPEDIA_DATASET_NAME, WIKIPEDIA_VERSION, TARGET_WORD_LIMIT, PATTERN_RU, PATTERN_EN, PATTERN_BE


class LexiconManager():
    def __init__(self, lang_code):
        self.lang_code = lang_code
        self.filename = f'freq_{lang_code}.json'
        self.word_counts = Counter()
        self.total_words_count = 0
        self.final_dict = {}
        self.load_words()


    def download_and_calculate(self):
        self.total_words_count = 0
        self.final_dict.clear()
        dataset = load_dataset(WIKIPEDIA_DATASET_NAME, f'{WIKIPEDIA_VERSION}.{self.lang_code}', split='train', trust_remote_code=True)
        match self.lang_code:
            case 'ru':
                current_pattern = PATTERN_RU
            case 'be':
                current_pattern = PATTERN_BE
            case 'en':
                current_pattern = PATTERN_EN
        for article in dataset:
            text_data = article['text']
            words_list = current_pattern.findall(text_data)
            words_list = [word.lower() for word in words_list]
            self.word_counts.update(words_list)
            self.total_words_count += len(words_list)
            if self.total_words_count >= TARGET_WORD_LIMIT:
                break
        if self.total_words_count < TARGET_WORD_LIMIT:
            print(f"Внимание: Корпус маловат! Собрано только {self.total_words_count} слов из {TARGET_WORD_LIMIT}")
        self.final_dict = dict(self.word_counts)
        self.save_words()


    def save_words(self):
        with open(self.filename, 'w', encoding='utf-8') as f:
            package = {
                'total_tokens': self.total_words_count,
                'dictionary': self.final_dict
            }
            json.dump(package, f, ensure_ascii=False, indent=4)


    def load_words(self):
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r', encoding='utf-8') as f:
                    package = json.load(f)
                    self.total_words_count = package.get('total_tokens', 0)
                    self.final_dict = package.get('dictionary', {})
            except Exception:
                self.final_dict = {}
                self.total_words_count = 0