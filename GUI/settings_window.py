from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTabWidget, QWidget)

from core.settings_handler import write_settings_to_json, get_resource_path


class SettingsWindow(QDialog):
    def __init__(self, parent=None, app=None, main_window=None, about_window=None, help_window=None):
        super().__init__(parent)
        self.parent = parent
        self.app = app
        self.about_window = about_window
        self.help_window = help_window
        self.height_label = None
        self.max_images_label = None
        self.value_columns_label = None
        self.cancel_button = None
        self.decimal_places = None
        self.main_window = main_window
        self.warning_label = None
        self.value_columns_input = None
        self.max_images_input = None
        self.height_input = None
        self.decimal_places_input = None
        self.setWindowTitle("Настройки")
        self.setGeometry(300, 300, 600, 400)
        self.setFixedSize(self.size())
        main_layout = QVBoxLayout()
        self.setWindowFlags(Qt.Window | Qt.WindowCloseButtonHint)

        tabs = QTabWidget()
        tabs.addTab(self.create_general_tab(), "Основные")

        main_layout.addWidget(tabs)
        main_layout.addLayout(self.create_buttons())

        self.setLayout(main_layout)

    def create_general_tab(self):
        general_tab = QWidget()
        layout = QVBoxLayout()

        width_layout = QHBoxLayout()
        self.decimal_places = QLabel("Количество знаков после запятой")
        from GUI.top_bar_with_icons import create_spin_box
        self.decimal_places_input = create_spin_box(1, 5, "decimal_places")
        width_layout.addWidget(self.decimal_places)
        width_layout.addWidget(self.decimal_places_input)

        layout.addLayout(width_layout)
        layout.addStretch(1)

        general_tab.setLayout(layout)
        return general_tab

    def create_buttons(self):
        button_layout = QHBoxLayout()
        icon_size = QSize(20, 20)
        ok_button = QPushButton("OK")
        ok_button.setIcon(QIcon(get_resource_path('assets/iconYes.png')))
        ok_button.setIconSize(icon_size)
        ok_button.setFixedHeight(40)
        ok_button.setFixedWidth(100)

        self.cancel_button = QPushButton(self.tr("Отмена"))
        self.cancel_button.setIcon(QIcon(get_resource_path('assets/iconCancel.png')))
        self.cancel_button.setIconSize(icon_size)
        self.cancel_button.setFixedHeight(40)
        self.cancel_button.setFixedWidth(100)

        button_layout.addStretch(1)
        button_layout.addWidget(ok_button)
        button_layout.addWidget(self.cancel_button)

        ok_button.clicked.connect(self.on_ok_button_clicked)
        self.cancel_button.clicked.connect(self.reject)

        return button_layout

    def on_ok_button_clicked(self):
        settings = {
            "decimal_places": self.decimal_places_input.value()
        }

        write_settings_to_json(settings)
        self.accept()