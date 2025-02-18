from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel
from PyQt5.QtGui import QMovie
from PyQt5.QtCore import Qt

from core.settings_handler import get_resource_path


class LoadingWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Загрузка')
        self.setFixedSize(300, 300)
        self.setStyleSheet("background-color: #ffffff;")
        self.setWindowFlags(Qt.Window | Qt.WindowTitleHint | Qt.CustomizeWindowHint)

        layout = QVBoxLayout()

        self.gif_label = QLabel(self)
        self.gif_label.setAlignment(Qt.AlignCenter)
        self.movie = QMovie(get_resource_path("assets/iconLoading.gif"))
        self.gif_label.setMovie(self.movie)
        layout.addWidget(self.gif_label)

        self.setLayout(layout)
        self.start_animation()

    def start_animation(self):
        self.movie.start()

    def stop_animation(self):
        self.movie.stop()
