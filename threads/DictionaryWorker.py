from PySide6.QtCore import QThread, Signal
from nlp.LexiconManager import LexiconManager
from config import DATASET_NAME, VERSION


class DictionaryWorker(QThread):
    progress = Signal(str)
    finished = Signal(dict, int, int)


    def __init__(self, lang_code):
        super().__init__()
        self.lang_code = lang_code
        self.manager = LexiconManager(lang_code)


    def run(self):
        if self.manager.final_dict:
            self.progress.emit(f'Succesfully loaded dictionary from JSON file, language = {self.lang_code}')
        else:
            self.progress.emit(f'Loading dicitonary from {DATASET_NAME}, version = {VERSION}, language = {self.lang_code}')
            self.manager.download_and_calculate()
            self.progress.emit(f'Succesully loaded dictionary from {DATASET_NAME}, version = {VERSION}, language = {self.lang_code}')
        self.finished.emit(self.manager.final_dict, self.manager.total_words_count, self.manager.total_unique_words_count)
            