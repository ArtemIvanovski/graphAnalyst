from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QIcon, QMovie
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel

from GUI.help_window import HelpWindow
from core.json_table_handler import JsonFileHandler
from core.settings_handler import get_resource_path


class GraphAnalystWindow(QWidget):
    def __init__(self):
        super().__init__()

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
        self.open_table_button = self.create_button("📊 Открыть график через таблицу", "assets/hint_table.gif")
        self.open_manual_button = self.create_button("📂 Открыть график вручную", "assets/hint_manual.gif")
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
