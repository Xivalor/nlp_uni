import re
import os
import json
from datasets import load_dataset
from collections import Counter
from config import DATASET_NAME, VERSION, TARGET_WORD_LIMIT, PATTERN_RU, PATTERN_EN, PATTERN_BE


class LexiconManager():

    def __init__(self, lang_code):
        self.lang_code = lang_code
        self.filename = f'freq_{lang_code}.json'
        self.word_counts = Counter()
        self.total_words_count = 0
        self.total_unique_words_count = 0
        self.final_dict = {}
        self.load_words()


    def download_and_calculate(self):
        self.total_words_count = 0
        self.total_unique_words_count = 0
        self.final_dict.clear()
        dataset = load_dataset(
            DATASET_NAME, 
            name=f'{VERSION}.{self.lang_code}', 
            split='train', 
            streaming=True
        )
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
            print(f"Warning: Not enough words! Collected only {self.total_words_count} of {TARGET_WORD_LIMIT} words")
        self.final_dict = dict(self.word_counts)
        self.total_unique_words_count = len(self.word_counts)
        self.save_words()


    def save_words(self):
        with open(self.filename, 'w', encoding='utf-8') as f:
            package = {
                'total_tokens': self.total_words_count,
                'total_unique_tokens': self.total_unique_words_count,
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
                    self.total_unique_words_count = package.get('total_unique_tokens', 0)
            except Exception:
                self.final_dict = {}
                self.total_words_count = 0
                self.total_unique_words_count = 0

    
    def get_sorted_words(self, by_frequency: bool, reverse: bool) -> dict:
        if by_frequency:
            return sorted(self.final_dict.items(), key=lambda x: (x[1], x[0]), reverse=reverse)
        else:
            return sorted(self.final_dict.items(), key=lambda x: (x[0], x[1]), reverse=reverse)
    
    
    def edit_dict(self, word=None, new_word=None, operation=None):
        match operation:
            case "Add word":
                if word not in self.final_dict:
                    self.final_dict[word] = 0
                else:
                    self.final_dict[word] += 1

                self.total_words_count += 1

            case "Delete word":
                if word in self.final_dict:
                    self.total_words_count -= self.final_dict[word]
                    self.final_dict.pop(word)

            case "Edit word":
                if word in self.final_dict:
                    self.final_dict[new_word] = (
                        self.final_dict.get(new_word, 0) + self.final_dict[word]
                    )
                    self.final_dict.pop(word)

        self.total_unique_words_count = len(self.final_dict)

        self.save_words()

    
    def add_text(self, text):
        match self.lang_code:
            case 'ru':
                current_pattern = PATTERN_RU
            case 'be':
                current_pattern = PATTERN_BE
            case 'en':
                current_pattern = PATTERN_EN

        words_list = current_pattern.findall(text)
        words_list = [word.lower() for word in words_list]

        for word in words_list:
            self.final_dict[word] = self.final_dict.get(word, 0) + 1

        self.total_words_count += len(words_list)
        self.total_unique_words_count = len(self.final_dict)

        self.save_words()