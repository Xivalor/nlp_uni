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
        self.setWindowTitle("Языковой Анализатор")
        self.resize(550, 600)