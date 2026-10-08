from PySide6.QtWidgets import QLineEdit
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget, 
    QVBoxLayout, 
    QHBoxLayout, 
    QPushButton, 
    QListWidget, 
    QLabel, 
    QComboBox,
    QRadioButton,
    QButtonGroup,
    QGroupBox,
    QDialog,
    QMessageBox,
)

from PySide6.QtCore import Qt, QTimer

from threads.DictionaryWorker import DictionaryWorker
from nlp.LexiconManager import LexiconManager 
from word_dialog import WordDialog
from text_dialog import TextDialog

from config import LANGUAGES


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("NLP")
        self.resize(550, 600)

        self.label_lang = QLabel("Select language:")
        self.combo_lang = QComboBox()
        self.combo_lang.addItems(LANGUAGES.keys())

        self.group_type = QButtonGroup(self)
        self.radio_freq = QRadioButton("By frequency")
        self.radio_alpha = QRadioButton("By alphabetical")

        self.group_type.addButton(self.radio_freq)
        self.group_type.addButton(self.radio_alpha)
        self.radio_freq.setChecked(True)

        self.group_order = QButtonGroup(self)
        self.radio_desc = QRadioButton("In descending order")
        self.radio_asc = QRadioButton("In ascending order")

        self.group_order.addButton(self.radio_desc)
        self.group_order.addButton(self.radio_asc)
        self.radio_desc.setChecked(True)

        self.radio_freq.toggled.connect(self.refresh_list)
        self.radio_alpha.toggled.connect(self.refresh_list)
        self.radio_desc.toggled.connect(self.refresh_list)
        self.radio_asc.toggled.connect(self.refresh_list)

        self.box_type = QGroupBox("Sorted by")
        box_type_layout = QVBoxLayout()

        box_type_layout.addWidget(self.radio_freq)
        box_type_layout.addWidget(self.radio_alpha)
        self.box_type.setLayout(box_type_layout)

        self.box_order = QGroupBox("In order")
        box_order_layout = QVBoxLayout()

        box_order_layout.addWidget(self.radio_desc)
        box_order_layout.addWidget(self.radio_asc)
        self.box_order.setLayout(box_order_layout)

        self.hbox_sorting = QHBoxLayout()
        self.hbox_sorting.addWidget(self.box_type)
        self.hbox_sorting.addWidget(self.box_order)

        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.setInterval(300)
        self.search_timer.timeout.connect(self.refresh_list)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Input text to find")
        self.search_input.textChanged.connect(self.search_timer.start)

        self.btn_load_data = QPushButton("Load data")
        self.btn_load_data.clicked.connect(self.load_data)

        self.label_status = QLabel("Waiting for choice...")
        self.label_words_count = QLabel("Words count: waiting for choice...")
        self.label_unique_words_count = QLabel("Unique words count: waiting for choice...")

        self.word_list = QListWidget()

        self.btn_edit_dict = QPushButton("Edit dictionary")
        self.btn_edit_dict.setEnabled(False)
        self.btn_edit_dict.clicked.connect(self.edit_dict_dialog)

        self.btn_add_text = QPushButton("Add text")
        self.btn_add_text.setEnabled(False)
        self.btn_add_text.clicked.connect(self.add_text_dialog)

        self.vboxlayout_main = QVBoxLayout()
        self.vboxlayout_main.addWidget(self.label_lang)
        self.vboxlayout_main.addWidget(self.combo_lang)
        self.vboxlayout_main.addLayout(self.hbox_sorting)
        self.vboxlayout_main.addWidget(self.search_input)
        self.vboxlayout_main.addWidget(self.btn_load_data)
        self.vboxlayout_main.addWidget(self.label_status)
        self.vboxlayout_main.addWidget(self.label_words_count)
        self.vboxlayout_main.addWidget(self.label_unique_words_count)
        self.vboxlayout_main.addWidget(self.word_list)
        self.vboxlayout_main.addWidget(self.btn_edit_dict)
        self.vboxlayout_main.addWidget(self.btn_add_text)

        central_widget = QWidget()
        central_widget.setLayout(self.vboxlayout_main)
        self.setCentralWidget(central_widget)

    
    def edit_dict_dialog(self):
        dialog = WordDialog(self)

        if dialog.exec():
            operation = dialog.operation.currentText()
            word = dialog.word_edit.text().lower()
            new_word = dialog.new_word_edit.text().lower()

            if operation == "Delete word":
                answer = QMessageBox.question(
                    self,
                    "Confirm delete",
                    f"Do you want to delete «{word}»?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )

                if answer != QMessageBox.Yes:
                    return

            self.active_manager.edit_dict(word=word, new_word=new_word, operation=operation)

            self.label_words_count.setText(
                f"Words count: {self.active_manager.total_words_count}"
            )

            self.label_unique_words_count.setText(
                f"Unique words count: {self.active_manager.total_unique_words_count}"
            )

            self.refresh_list()


    def add_text_dialog(self):
        dialog = TextDialog(self)

        if dialog.exec():
            text = dialog.text_edit.toPlainText()

            if not text.strip():
                return

            self.active_manager.add_text(text)

            self.label_words_count.setText(
                f"Words count: {self.active_manager.total_words_count}"
            )

            self.label_unique_words_count.setText(
                f"Unique words count: {self.active_manager.total_unique_words_count}"
            )

            self.refresh_list()


    def load_data(self):
        selected_lang = LANGUAGES[self.combo_lang.currentText()]

        self.worker = DictionaryWorker(selected_lang)

        self.worker.progress.connect(self.update_status)        
        self.worker.finished.connect(self.handle_results)

        self.btn_load_data.setEnabled(False)
        self.worker.start()

    
    def update_status(self, message_text):
        self.label_status.setText(message_text)


    def handle_results(self, result_dict, words_count, unique_words_count):
        self.btn_load_data.setEnabled(True)
        self.btn_edit_dict.setEnabled(True)
        self.btn_add_text.setEnabled(True)
        self.word_list.clear()
        self.label_words_count.setText(f"Words count: {words_count}")
        self.label_unique_words_count.setText(f"Unique words count: {unique_words_count}")
        ui_lines = [f"{word}: {count}" for word, count in result_dict.items()]
        self.word_list.addItems(ui_lines)
        self.active_manager = self.worker.manager
        self.refresh_list()

    
    def refresh_list(self):
        if not hasattr(self, 'active_manager'):
            return
        
        by_freq = self.radio_freq.isChecked()
        is_reverse = self.radio_desc.isChecked()

        self.word_list.clear()
        sorted_items = self.active_manager.get_sorted_words(by_freq, is_reverse)
        search_text = self.search_input.text().lower()
        if search_text:
            ui_lines = [f"{word}: {count}" for word, count in sorted_items if search_text in word]
        else:
            ui_lines = [f"{word}: {count}" for word, count in sorted_items]
        self.word_list.addItems(ui_lines)