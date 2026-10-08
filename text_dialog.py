from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QTextEdit,
    QPushButton
)


class TextDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Add text")
        self.resize(500, 350)

        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Enter new text:"))

        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("Enter or paste text...")
        layout.addWidget(self.text_edit)

        buttons = QHBoxLayout()

        self.ok_button = QPushButton("OK")
        self.cancel_button = QPushButton("Cancel")

        buttons.addWidget(self.ok_button)
        buttons.addWidget(self.cancel_button)

        layout.addLayout(buttons)

        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)