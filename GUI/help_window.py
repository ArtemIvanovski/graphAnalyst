import os
from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QWidget, QTreeWidget, QTreeWidgetItem, QSplitter, \
    QTextBrowser
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QIcon

from core.settings_handler import get_resource_path
from logger import logger


class HelpWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Graph Analyst")
        self.setGeometry(100, 100, 800, 600)
        self.setWindowIcon(QIcon(get_resource_path('assets/icon.png')))

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)

        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.itemClicked.connect(self.on_tree_item_clicked)
        splitter.addWidget(self.tree)

        self.text_browser = QTextBrowser()
        splitter.addWidget(self.text_browser)

        self.create_tree()

        self.load_initial_content()

    def create_tree(self):
        contents = QTreeWidgetItem(self.tree, ["Содержание"])

        sections = [
            ("Главная страница", "home.html"),
            ("Открытие графика через поиск", "open_graph_use_search.html"),
            ("Открытие графика вручную", "open_graph_manual.html"),
            ("Открытие графика через таблицу", "open_graph_use_table.html"),
            ("Работа с графиком", "graph_work.html")
        ]

        for title, file in sections:
            item = QTreeWidgetItem(contents, [title])
            item.setData(0, Qt.UserRole, file)

        self.tree.addTopLevelItem(contents)
        self.tree.expandAll()

    def load_initial_content(self):
        self.load_html("home.html")

    def on_tree_item_clicked(self, item):
        file = item.data(0, Qt.UserRole)
        if file:
            self.load_html(file)

    def load_html(self, file_name):
        base_dir = os.path.dirname(__file__)
        help_dir = os.path.join(base_dir, 'help_html')
        file_path = os.path.join(help_dir, file_name)

        try:
            with open(get_resource_path(file_path), 'r', encoding='utf-8') as file:
                html_content = file.read()

                self.text_browser.setSearchPaths([help_dir])

                self.text_browser.setHtml(html_content)

        except FileNotFoundError:
            self.text_browser.setHtml("<h1>404</h1><p>Page not found</p>")
            logger.error("Page not found: " + file_name)
