from PySide6.QtWidgets import (
    QMainWindow,
    QWidget, 
    QVBoxLayout, 
    QHBoxLayout, 
    QPushButton, 
    QListWidget, 
    QLabel, 
    QComboBox
)

from PySide6.QtCore import Qt

from threads import DictionaryWorker
from nlp import LexiconManager 


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("NLP")
        self.resize(550, 600)

        self.combo_lang = QComboBox()
        self.combo_lang.addItems(["ru, en, be"])

        self.btn_load_data = QPushButton("Load data")
        self.btn_load_data.connect(self.load_data)

        self.label_status = QLabel("Waiting for choice...")

        self.word_list = QListWidget()

        self.vboxlayout_main = QVBoxLayout()
        self.vboxlayout_main.add(self.combo_lang)
        self.vboxlayout_main.add(self.btn_load_data)
        self.vboxlayout_main.add(self.label_status)
        self.vboxlayout_main.add(self.word_list)


    def start_processing(self):
        selected_lang = self.combo_lang.currentText()

        self.worker = DictionaryWorker(selected_lang)

        self.worker.progress.connect(self.update_status)        
        self.worker.finished.connect(self.handle_results)

        self.btn_load_data.setEnabled(False)
        self.worker.start()

    
    def update_status(self, message_text):
        self.label_status.setText(message_text)


    def handle_results(self, result_dict):
        self.btn_load_data.setEnabled(True)
        self.word_list.clear()
        ui_lines = [f"{word}: {count}" for word, count in result_dict.items()]
        self.word_list.addItems(ui_lines[:500])