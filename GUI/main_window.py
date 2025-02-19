import os

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QIcon, QMovie
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QFileDialog

from GUI.error_window import ErrorWindow
from GUI.graph_window import GraphWindow
from GUI.help_window import HelpWindow
from GUI.loading_window import LoadingWindow
from GUI.search_window import SearchWindow
from GUI.table_window import TableWindow
from core.data_frame_utils import validate_file_format
from core.json_table_handler import JsonFileHandler
from core.settings_handler import get_resource_path
from core.threads.file_processing_thread import FileProcessingThread


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.search_window = None
        self.file_processing_thread = None
        self.loading_window = None
        self.file_path = None
        self.table_window = None
        self.help_window = None
        self.json_file_handler = JsonFileHandler(get_resource_path("library/table.json"))
        self.setWindowTitle("Graph Analyst")
        self.setWindowIcon(QIcon(get_resource_path("assets/icon.png")))
        self.setGeometry(200, 200, 600, 400)

        title_font = QFont("Arial", 18, QFont.Bold)

        self.title_label = QLabel("Graph Analyst", self)
        self.title_label.setFont(title_font)
        self.title_label.setAlignment(Qt.AlignCenter)

        self.open_search_button = self.create_button("🔍 Открыть график через поиск", "assets/hint_search.gif")
        self.open_search_button.clicked.connect(self.show_search_window)

        self.open_table_button = self.create_button("📊 Открыть график через таблицу", "assets/hint_table.gif")
        self.open_table_button.clicked.connect(self.show_table_window)

        self.open_manual_button = self.create_button("📂 Открыть график вручную", "assets/hint_manual.gif")
        self.open_manual_button.clicked.connect(self.open_manual_graph)

        self.user_guide_button = self.create_button("📖 Руководство пользователя", None)
        self.user_guide_button.clicked.connect(self.show_help_window)

        layout = QVBoxLayout()
        layout.addWidget(self.title_label)
        layout.addSpacing(20)
        layout.addWidget(self.open_search_button)
        layout.addWidget(self.open_table_button)
        layout.addWidget(self.open_manual_button)
        layout.addWidget(self.user_guide_button)

        self.setLayout(layout)

        self.tooltip_label = QLabel(self)
        self.tooltip_label.setWindowFlags(Qt.ToolTip)
        self.tooltip_label.setAlignment(Qt.AlignCenter)
        self.tooltip_label.setScaledContents(True)
        self.tooltip_label.hide()

    def create_button(self, text, hint_gif_path):
        button = QPushButton(text, self)
        button.setFont(QFont("Arial", 12))
        button.setStyleSheet("""
            QPushButton {
                background-color: #0078D7;
                color: white;
                border-radius: 10px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #005A9E;
            }
        """)

        if hint_gif_path:
            button.enterEvent = lambda event, gif=hint_gif_path: self.show_gif_hint(event, gif)
            button.leaveEvent = lambda event: self.hide_gif_hint()

        return button

    def show_gif_hint(self, event, gif_path):
        self.tooltip_label.setMovie(QMovie(get_resource_path(gif_path)))
        self.tooltip_label.movie().start()
        self.tooltip_label.setGeometry(event.globalX() + 20, event.globalY() - 50, 200, 120)
        self.tooltip_label.show()

    def hide_gif_hint(self):
        self.tooltip_label.hide()

    def show_help_window(self):
        if not self.help_window:
            self.help_window = HelpWindow(self)
        self.help_window.show()

    def show_table_window(self):
        if not self.table_window:
            self.table_window = TableWindow(self.json_file_handler)
        self.table_window.show()

    def show_search_window(self):
        if not self.search_window:
            self.search_window = SearchWindow(self.json_file_handler)
        self.search_window.show()

    def open_manual_graph(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите файл .txt",
            "./library/",
            "Text Files (*.txt)"
        )
        if not file_path:
            return

        if not validate_file_format(file_path):
            error_dialog = ErrorWindow("Неверный формат файла. Пожалуйста, выберите корректный файл.")
            error_dialog.exec_()
            return
        self.file_path = file_path
        self.start_processing(file_path)

    def start_processing(self, file_path):
        self.loading_window = LoadingWindow(self)
        self.loading_window.show()

        self.file_processing_thread = FileProcessingThread(file_path, self.json_file_handler)
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
        self.graph_window = GraphWindow(metadata, data_frame, os.path.basename(self.file_path))
        self.graph_window.show()
