from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QSpinBox, QPushButton, QTextEdit, QProgressBar,
                             QMessageBox, QFileDialog)
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtGui import QIcon, QFont

from core.poster_processor import PosterProcessor
from core.settings_handler import get_resource_path
import os


class BatchPosterThread(QThread):
    progress_updated = pyqtSignal(str)
    finished_signal = pyqtSignal(list, str)

    def __init__(self, poster_processor, sample_number, output_folder):
        super().__init__()
        self.poster_processor = poster_processor
        self.sample_number = sample_number
        self.output_folder = output_folder

    def run(self):
        try:
            created_posters, folder = self.poster_processor.create_sample_posters_batch(
                self.sample_number, self.output_folder
            )
            self.finished_signal.emit(created_posters, folder)
        except Exception as e:
            self.progress_updated.emit(f"Ошибка: {str(e)}")


class BatchPosterWindow(QDialog):
    def __init__(self, json_file_handler, parent=None):
        super().__init__(parent)
        self.json_file_handler = json_file_handler
        self.poster_processor = None
        self.batch_thread = None

        self.setWindowTitle("Пакетное создание плакатов")
        self.setWindowIcon(QIcon(get_resource_path("assets/icon.png")))
        self.resize(600, 500)

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Заголовок
        title = QLabel("Автоматическое создание плакатов для образца")
        title_font = QFont("Arial", 14, QFont.Bold)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Описание
        description = QLabel(
            "Создаст 12 плакатов для выбранного образца:\n"
            "• 3 времени (2, 5, 10 мс)\n"
            "• 2 локализации (вестибулярная, пришеечная)\n"
            "• 2 интенсивности (слабая, сильная)\n"
            "• С применением ВЧ фильтра 500 Гц, порядок 3"
        )
        description.setStyleSheet("QLabel { background-color: #f0f0f0; padding: 10px; border-radius: 5px; }")
        layout.addWidget(description)

        sample_layout = QHBoxLayout()
        sample_layout.addWidget(QLabel("Номер образца:"))

        self.sample_spinbox = QSpinBox()
        self.sample_spinbox.setRange(41, 50)
        self.sample_spinbox.setValue(41)
        sample_layout.addWidget(self.sample_spinbox)

        sample_layout.addStretch()
        layout.addLayout(sample_layout)

        folder_layout = QHBoxLayout()
        folder_layout.addWidget(QLabel("Папка сохранения:"))

        self.folder_button = QPushButton("Выбрать папку...")
        self.folder_button.clicked.connect(self.select_output_folder)
        folder_layout.addWidget(self.folder_button)

        self.selected_folder = None
        layout.addLayout(folder_layout)

        buttons_layout = QHBoxLayout()

        self.start_button = QPushButton("🚀 Начать создание плакатов")
        self.start_button.clicked.connect(self.start_batch_creation)
        self.start_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #45a049; }
        """)
        buttons_layout.addWidget(self.start_button)

        self.cancel_button = QPushButton("Отмена")
        self.cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(self.cancel_button)

        layout.addLayout(buttons_layout)

        # Лог прогресса
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(200)
        self.log_text.setReadOnly(True)
        layout.addWidget(QLabel("Прогресс:"))
        layout.addWidget(self.log_text)

        self.setLayout(layout)

    def select_output_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Выберите папку для сохранения плакатов")
        if folder:
            self.selected_folder = folder
            self.folder_button.setText(f"📁 {os.path.basename(folder)}")

    def start_batch_creation(self):
        sample_number = self.sample_spinbox.value()

        output_folder = self.selected_folder
        if not output_folder:
            output_folder = get_resource_path(f"posters_sample_{sample_number}")

        self.log_text.clear()
        self.log_text.append(f"Начинаем создание плакатов для образца {sample_number}")
        self.log_text.append(f"Папка сохранения: {output_folder}")
        self.log_text.append("Применяется ВЧ фильтр 500 Гц, порядок 3\n")

        self.start_button.setEnabled(False)
        self.start_button.setText("⏳ Создание плакатов...")

        self.poster_processor = PosterProcessor(self.json_file_handler)

        self.batch_thread = BatchPosterThread(self.poster_processor, sample_number, output_folder)
        self.batch_thread.progress_updated.connect(self.update_log)
        self.batch_thread.finished_signal.connect(self.on_batch_finished)
        self.batch_thread.start()

    def update_log(self, message):
        self.log_text.append(message)
        self.log_text.ensureCursorVisible()

    def on_batch_finished(self, created_posters, output_folder):
        self.start_button.setEnabled(True)
        self.start_button.setText("🚀 Начать создание плакатов")

        success_count = len(created_posters)
        self.log_text.append(f"\n✅ Завершено! Создано {success_count} плакатов")
        self.log_text.append(f"📁 Сохранено в: {output_folder}")

        QMessageBox.information(
            self,
            "Создание завершено",
            f"Успешно создано {success_count} плакатов\nСохранено в: {output_folder}"
        )