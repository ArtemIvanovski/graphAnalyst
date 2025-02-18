from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QFontMetrics
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QDialogButtonBox

from core.settings_handler import get_resource_path


class ErrorWindow(QDialog):
    def __init__(self, message):
        super().__init__()
        self.setWindowTitle('Ошибка')
        self.setWindowIcon(QIcon(get_resource_path('assets/iconError.png')))
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        layout = QVBoxLayout()
        label = QLabel(message)
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok)
        button_box.accepted.connect(self.accept)
        layout.addWidget(button_box)

        self.setLayout(layout)

        font_metrics = QFontMetrics(label.font())
        text_rect = font_metrics.boundingRect(label.text())
        new_width = text_rect.width() + 100
        new_height = text_rect.height() + button_box.sizeHint().height() + 50
        self.resize(new_width, new_height)
