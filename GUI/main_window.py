from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QFileDialog, QApplication

from GUI.error_window import ErrorWindow
from GUI.graph_window import GraphWindow
from GUI.loading_window import LoadingWindow
from GUI.top_bar_with_icons import create_top_bar_with_icons, create_button
from core.data_frame_utils import validate_file_format
from core.settings_handler import get_resource_path
from core.threads.file_processing_thread import FileProcessingThread
from logger import logger


class MainWindow(QMainWindow):
    def __init__(self, app):
        super().__init__()
        self.app = app

        self.setWindowTitle("Graph Analyst")
        self.setStyleSheet("background-color: #f3f3f3;")
        self.setWindowIcon(QIcon(get_resource_path("assets/icon.png")))

        screen_geometry = QApplication.desktop().screenGeometry()
        self.screen_width = screen_geometry.width()
        self.screen_height = screen_geometry.height()
        self.setFixedSize(self.screen_width, self.screen_height)

        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        self.layout = QVBoxLayout()

        white_strip, grey_strip, _, _ = create_top_bar_with_icons(self, None, None, app, None)

        self.layout.addWidget(white_strip)
        self.layout.addWidget(grey_strip)

        button_layout = QHBoxLayout()
        self.select_file_button = create_button("Выбрать файл", get_resource_path("assets/iconAddFile.png"))
        self.select_file_button.clicked.connect(self.select_file)
        button_layout.addWidget(self.select_file_button)

        self.layout.addLayout(button_layout)
        self.main_widget.setLayout(self.layout)

        self.loading_window = None
        self.file_processing_thread = None

    def select_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Выберите файл .txt", "", "Text Files (*.txt)")
        if not file_path:
            return

        if not validate_file_format(file_path):
            error_dialog = ErrorWindow("Неверный формат файла. Пожалуйста, выберите корректный файл.")
            error_dialog.exec_()
            return

        self.start_processing(file_path)

    def start_processing(self, file_path):
        self.loading_window = LoadingWindow(self)
        self.loading_window.show()

        self.file_processing_thread = FileProcessingThread(file_path)
        self.file_processing_thread.finished.connect(self.on_processing_finished)
        self.file_processing_thread.start()

    def on_processing_finished(self, metadata, status):
        self.loading_window.close()

        if status == "error":
            error_dialog = ErrorWindow(f"Ошибка обработки файла: {metadata.get('error', 'Неизвестная ошибка')}")
            error_dialog.exec_()
            return

        data_frame = self.file_processing_thread.data_frame
        self.open_graph_window(metadata, data_frame)

    def open_graph_window(self, metadata, data_frame):
        self.graph_window = GraphWindow(metadata, data_frame, self, self.app)
        self.graph_window.show()
        self.hide()

    def showEvent(self, event):
        self.showMaximized()
        self.setFixedSize(self.screen_width, self.screen_height)
        super().showEvent(event)