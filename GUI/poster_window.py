import os
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton,
    QHBoxLayout, QLabel, QComboBox, QGroupBox, QMessageBox
)

from GUI.error_window import ErrorWindow
from GUI.loading_window import LoadingWindow
from GUI.poster_viewer_window import PosterViewerWindow
from core.threads.poster_processing_thread import PosterProcessingThread
from core.settings_handler import get_resource_path


class PosterWindow(QWidget):
    def __init__(self, json_file_handler):
        super().__init__()
        self.setWindowTitle("Создать плакат")
        self.setWindowIcon(QIcon(get_resource_path("assets/icon.png")))
        self.setGeometry(200, 200, 600, 300)

        self.json_file_handler = json_file_handler
        self.poster_processing_thread = None
        self.loading_window = None
        self.poster_viewer_window = None
        self.current_selected_params = None

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        title_label = QLabel("Создание плаката")
        title_font = QFont("Arial", 16, QFont.Bold)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        params_group = QGroupBox("")
        params_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 8px;
                margin-top: 1ex;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #333;
            }
        """)
        params_layout = QVBoxLayout()

        filters_layout = QHBoxLayout()

        left_column = QVBoxLayout()
        sample_layout = QHBoxLayout()
        sample_layout.addWidget(QLabel("Образец:"))
        self.sample_filter = self.create_filter("sample", self.json_file_handler.get_all_values_for_key("sample"))
        sample_layout.addWidget(self.sample_filter)
        left_column.addLayout(sample_layout)

        localization_layout = QHBoxLayout()
        localization_layout.addWidget(QLabel("Локализация:"))
        self.localization_filter = self.create_filter("localization",
                                                      self.json_file_handler.get_all_values_for_key("localization"))
        localization_layout.addWidget(self.localization_filter)
        left_column.addLayout(localization_layout)

        right_column = QVBoxLayout()
        time_layout = QHBoxLayout()
        time_layout.addWidget(QLabel("Время:"))
        self.time_filter = self.create_filter("time_ms", self.json_file_handler.get_all_values_for_key("time_ms"))
        time_layout.addWidget(self.time_filter)
        right_column.addLayout(time_layout)

        intensity_layout = QHBoxLayout()
        intensity_layout.addWidget(QLabel("Интенсивность:"))
        self.intensity_filter = self.create_filter("intensity",
                                                   self.json_file_handler.get_all_values_for_key("intensity"))
        intensity_layout.addWidget(self.intensity_filter)
        right_column.addLayout(intensity_layout)

        filters_layout.addLayout(left_column)
        filters_layout.addLayout(right_column)

        params_layout.addLayout(filters_layout)
        params_group.setLayout(params_layout)
        layout.addWidget(params_group)

        self.create_poster_button = QPushButton("Создать плакат", self)
        self.create_poster_button.setFont(QFont("Arial", 12, QFont.Bold))
        self.create_poster_button.setStyleSheet("""
            QPushButton {
                background-color: #0078D7;
                color: white;
                border-radius: 8px;
                padding: 12px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #005A9E;
            }
            QPushButton:pressed {
                background-color: #1e7e34;
            }
        """)
        self.create_poster_button.clicked.connect(self.create_poster)
        layout.addWidget(self.create_poster_button)

        self.setLayout(layout)

    def create_filter(self, key, options):
        combo = QComboBox(self)
        combo.setStyleSheet("""
            QComboBox {
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 5px;
                background-color: white;
            }
            QComboBox:hover {
                border-color: #0078D7;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 6px solid #666;
                margin-right: 6px;
            }
        """)
        combo.addItems(options)
        combo.key = key
        return combo

    def create_poster(self):
        selected_params = {
            "sample": self.sample_filter.currentText(),
            "time_ms": self.time_filter.currentText(),
            "localization": self.localization_filter.currentText(),
            "intensity": self.intensity_filter.currentText()
        }

        if not all(selected_params.values()):
            error_dialog = ErrorWindow("Пожалуйста, выберите все параметры")
            error_dialog.exec_()
            return

        pickling_times = ["без протравливания", "15 с", "30 с", "45 с", "60 с"]
        missing_files = []

        for pickling_time in pickling_times:
            filters = selected_params.copy()
            filters["pickling_time"] = pickling_time

            results = self.json_file_handler.search_entries("", filters)

            if not results:
                missing_files.append(pickling_time)

        if missing_files:
            error_msg = f"Не найдены файлы для времени протравливания: {', '.join(missing_files)}"
            error_dialog = ErrorWindow(error_msg)
            error_dialog.exec_()
            return

        self.current_selected_params = selected_params
        self.start_poster_processing(selected_params)

    def start_poster_processing(self, selected_params):
        self.loading_window = LoadingWindow(self)
        self.loading_window.show()

        self.poster_processing_thread = PosterProcessingThread(selected_params, self.json_file_handler)
        self.poster_processing_thread.finished.connect(self.on_poster_processing_finished)
        self.poster_processing_thread.start()

    def on_poster_processing_finished(self, final_poster_path, temp_folder, status):
        self.loading_window.close()

        if status.startswith("error"):
            error_dialog = ErrorWindow(f"Ошибка создания плаката: {status}")
            error_dialog.exec_()
            return

        if final_poster_path and os.path.exists(final_poster_path):
            self.poster_viewer_window = PosterViewerWindow(
                final_poster_path,
                temp_folder,
                self.current_selected_params,
                self
            )
            self.poster_viewer_window.show()
        else:
            error_dialog = ErrorWindow("Не удалось создать плакат")
            error_dialog.exec_()