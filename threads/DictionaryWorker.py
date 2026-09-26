from PySide6.QtCore import QThread, Signal
from nlp.LexiconManager import LexiconManager
from config import DATASET_NAME, VERSION


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
            self.progress.emit(f'Loading dicitonary from {DATASET_NAME}, version = {VERSION}')
            self.manager.download_and_calculate()
            self.progress.emit(f'Succesully loaded dictionary from {DATASET_NAME}, version = {VERSION}')
        self.finished.emit(self.manager.final_dict)
            