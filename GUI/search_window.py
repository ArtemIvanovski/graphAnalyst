import os

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLineEdit, QListWidget, QPushButton,
    QHBoxLayout, QLabel, QComboBox
)

from core.proccesing_mixin import ProcessingMixin
from core.settings_handler import get_resource_path


class SearchWindow(QWidget, ProcessingMixin):
    def __init__(self, json_file_handler):
        super().__init__()
        self.filename = None
        self.setWindowTitle("Graph Analyst")
        self.setWindowIcon(QIcon(get_resource_path("assets/icon.png")))
        self.setGeometry(200, 200, 600, 500)

        self.json_file_handler = json_file_handler

        self.init_ui()

    def init_ui(self):
        """Создает UI элементов."""
        layout = QVBoxLayout()

        # Поисковая строка
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit(self)
        self.search_input.setPlaceholderText("Введите запрос...")
        self.search_input.textChanged.connect(self.search)
        search_layout.addWidget(QLabel("🔎"))
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)
        filters_layout = QHBoxLayout()

        filters_layout = QHBoxLayout()

        self.sample_filter = self.create_filter("sample",
                                                ["Не важно"] + self.json_file_handler.get_all_values_for_key("sample"))
        self.time_filter = self.create_filter("time_ms",
                                              ["Не важно"] + self.json_file_handler.get_all_values_for_key("time_ms"))
        self.type_filter = self.create_filter("type",
                                              ["Не важно"] + self.json_file_handler.get_all_values_for_key("type"))
        self.type2_filter = self.create_filter("type_2",
                                               ["Не важно"] + self.json_file_handler.get_all_values_for_key("type_2"))
        self.subtype_filter = self.create_filter("subtype",
                                                 ["Не важно"] + self.json_file_handler.get_all_values_for_key(
                                                     "subtype"))

        filters_layout.addWidget(QLabel("Sample:"))
        filters_layout.addWidget(self.sample_filter)
        filters_layout.addWidget(QLabel("Time:"))
        filters_layout.addWidget(self.time_filter)
        filters_layout.addWidget(QLabel("Type:"))
        filters_layout.addWidget(self.type_filter)
        filters_layout.addWidget(QLabel("Type2:"))
        filters_layout.addWidget(self.type2_filter)
        filters_layout.addWidget(QLabel("Subtype:"))
        filters_layout.addWidget(self.subtype_filter)

        self.results_list = QListWidget(self)

        self.open_button = QPushButton("Открыть", self)
        self.open_button.clicked.connect(self.open_selected_file)

        layout.addWidget(self.search_input)
        layout.addLayout(filters_layout)
        layout.addWidget(self.results_list)
        layout.addWidget(self.open_button)

        self.setLayout(layout)

    def create_filter(self, key, options):
        combo = QComboBox(self)
        combo.addItems(options)
        combo.currentIndexChanged.connect(self.search)
        combo.key = key
        return combo

    def search(self):
        query = self.search_input.text().lower()

        filters = {
            "sample": self.sample_filter.currentText(),
            "time_ms": self.time_filter.currentText(),
            "type": self.type_filter.currentText(),
            "type_2": self.type2_filter.currentText(),
            "subtype": self.subtype_filter.currentText(),
        }

        results = self.json_file_handler.search_entries(query, filters)
        self.results_list.clear()

        for entry in results:
            display_text = f"{entry['filename']} | {entry['sample']} | {entry['time_ms']} | {entry['type']} | {entry['type_2']} | {entry['subtype']}"
            self.results_list.addItem(display_text)

    def open_selected_file(self):
        selected_item = self.results_list.currentItem()
        if selected_item:
            self.filename = selected_item.text().split(" | ")[0]
            filepath = os.path.join("./library/", self.filename)
            self.start_processing(filepath)

