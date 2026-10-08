from config import OPERATIONS
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QComboBox
)


class WordDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Edit dictionary")
        self.resize(350, 220)

        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Operation:"))

        self.operation = QComboBox()
        self.operation.addItems(OPERATIONS)
        layout.addWidget(self.operation)

        layout.addWidget(QLabel("Word:"))

        self.word_edit = QLineEdit()
        layout.addWidget(self.word_edit)

        self.new_word_label = QLabel("New word:")

        self.new_word_edit = QLineEdit()

        layout.addWidget(self.new_word_label)
        layout.addWidget(self.new_word_edit)

        buttons = QHBoxLayout()

        self.ok_button = QPushButton("OK")
        self.cancel_button = QPushButton("Cancel")

        buttons.addWidget(self.ok_button)
        buttons.addWidget(self.cancel_button)

        layout.addLayout(buttons)

        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

        self.operation.currentTextChanged.connect(
            self.operation_changed
        )

        self.operation_changed(self.operation.currentText())

    def operation_changed(self, operation):
        if operation == "Edit word":
            self.new_word_label.show()
            self.new_word_edit.show()
        else:
            self.new_word_label.hide()
            self.new_word_edit.hide()