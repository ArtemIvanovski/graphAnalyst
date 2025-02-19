from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout

from core.settings_handler import get_resource_path


class MetadataWindow(QDialog):

    def __init__(self, metadata, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Window | Qt.WindowCloseButtonHint)

        self.setWindowTitle(self.tr("Метаданные"))
        self.setFixedSize(400, 500)
        self.setWindowIcon(QIcon(get_resource_path("assets/icon.png")))

        layout = QVBoxLayout()

        title_label = QLabel("Метаданные")
        title_font = QFont("Arial", 16, QFont.Bold)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        if metadata:
            for key, value in metadata.items():
                metadata_label = QLabel(f"<b>{key}:</b> {value}")
                metadata_label.setWordWrap(True)
                layout.addWidget(metadata_label)
        else:
            no_data_label = QLabel("Нет метаданных для отображения.")
            no_data_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(no_data_label)

        ok_button = QPushButton("OK")
        ok_button.setFixedHeight(40)
        ok_button.setFixedWidth(100)
        ok_button.clicked.connect(self.accept)
        ok_button_layout = QHBoxLayout()
        ok_button_layout.addStretch()
        ok_button_layout.addWidget(ok_button)
        ok_button_layout.addStretch()
        layout.addLayout(ok_button_layout)

        self.setLayout(layout)

