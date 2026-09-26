from PySide6.QtCore import QThread, Signal
from nlp.LexiconManager import LexiconManager
from config import WIKIPEDIA_DATASET_NAME, WIKIPEDIA_VERSION


class DictionaryWorker(QThread):
    progress = Signal(str)
    finished = Signal(dict)


    def __init__(self, lang_code):
        super().__init__()
        self.lang_code = lang_code
        self.manager = LexiconManager(lang_code)

    
    def run(self):
        if self.manager.final_dict:
            self.progress.emit('Succesfully loaded dictionary from JSON file')
        else:
            self.progress.emit(f'Loading dicitonary from {WIKIPEDIA_DATASET_NAME}, version = {WIKIPEDIA_VERSION}')
            self.manager.download_and_calculate()
            self.progress.emit(f'Succesully loaded dictionary from {WIKIPEDIA_DATASET_NAME}, version = {WIKIPEDIA_VERSION}')
        self.finished.emit(self.manager.final_dict)
            