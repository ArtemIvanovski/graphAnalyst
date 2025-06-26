import os

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QFileDialog

from GUI.error_window import ErrorWindow
from GUI.help_window import HelpWindow
from GUI.poster_window import PosterWindow
from GUI.search_window import SearchWindow
from GUI.table_window import TableWindow
from core.data_frame_utils import validate_file_format
from core.json_table_handler import JsonFileHandler
from core.proccesing_mixin import ProcessingMixin
from core.settings_handler import get_resource_path


class MainWindow(QWidget, ProcessingMixin):
    def __init__(self):
        super().__init__()
        self.child_windows = []
        self.filename = None
        self.search_window = None
        self.file_processing_thread = None
        self.loading_window = None
        self.file_path = None
        self.table_window = None
        self.help_window = None
        self.poster_window = None
        self.json_file_handler = JsonFileHandler(get_resource_path("library/table.json"))
        self.setWindowTitle("Graph Analyst")
        self.setWindowIcon(QIcon(get_resource_path("assets/icon.png")))
        self.setGeometry(200, 200, 600, 450)

        title_font = QFont("Arial", 18, QFont.Bold)

        self.title_label = QLabel("Graph Analyst", self)
        self.title_label.setFont(title_font)
        self.title_label.setAlignment(Qt.AlignCenter)

        self.open_search_button = self.create_button("🔍 Открыть график через поиск")
        self.open_search_button.clicked.connect(self.show_search_window)

        self.open_table_button = self.create_button("📊 Открыть график через таблицу")
        self.open_table_button.clicked.connect(self.show_table_window)

        self.open_manual_button = self.create_button("📂 Открыть график вручную")
        self.open_manual_button.clicked.connect(self.open_manual_graph)

        self.create_poster_button = self.create_button("📊 Создать плакат")
        self.create_poster_button.clicked.connect(self.show_poster_window)

        self.user_guide_button = self.create_button("📖 Руководство пользователя")
        self.user_guide_button.clicked.connect(self.show_help_window)

        layout = QVBoxLayout()
        layout.addWidget(self.title_label)
        layout.addSpacing(20)
        layout.addWidget(self.open_search_button)
        layout.addWidget(self.open_table_button)
        layout.addWidget(self.open_manual_button)
        layout.addWidget(self.create_poster_button)
        layout.addWidget(self.user_guide_button)

        self.setLayout(layout)

        self.tooltip_label = QLabel(self)
        self.tooltip_label.setWindowFlags(Qt.ToolTip)
        self.tooltip_label.setAlignment(Qt.AlignCenter)
        self.tooltip_label.setScaledContents(True)
        self.tooltip_label.hide()

    def create_button(self, text):
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
        return button

    def show_help_window(self):
        if not self.help_window:
            self.help_window = HelpWindow(self)
        self.help_window.show()
        self.child_windows.append(self.help_window)

    def show_table_window(self):
        if not self.table_window:
            self.table_window = TableWindow(self.json_file_handler)
        self.table_window.show()
        self.child_windows.append(self.table_window)

    def show_search_window(self):
        if not self.search_window:
            self.search_window = SearchWindow(self.json_file_handler)
        self.search_window.show()
        self.child_windows.append(self.search_window)

    def show_poster_window(self):
        if not hasattr(self, 'poster_window') or not self.poster_window:
            self.poster_window = PosterWindow(self.json_file_handler)
        self.poster_window.show()
        self.child_windows.append(self.poster_window)

    def open_manual_graph(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Выберите файл .txt", get_resource_path("library/"), "Text Files (*.txt)"
        )
        if not file_path:
            return

        if not validate_file_format(file_path):
            error_dialog = ErrorWindow("Неверный формат файла. Пожалуйста, выберите корректный файл.")
            error_dialog.exec_()
            return

        self.file_path = file_path
        self.filename = os.path.basename(self.file_path)
        self.start_processing(file_path)

    def closeEvent(self, event):
        for window in self.child_windows:
            if window.isVisible():
                window.close()

        event.accept()