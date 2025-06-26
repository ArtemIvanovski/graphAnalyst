import os

from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QFont, QColor, QBrush, QIcon
from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget, QAction, QMenu

from GUI.table_utils import make_bold, get_param_coil
from core.proccesing_mixin import ProcessingMixin
from core.settings_handler import get_resource_path


class TableWindow(QWidget, ProcessingMixin):
    def __init__(self, json_file_handler):
        super().__init__()
        self.filename = None
        self.graph_window = None
        self.file_processing_thread = None
        self.loading_window = None
        self.setWindowTitle("Таблица файлов")
        self.setWindowIcon(QIcon(get_resource_path("assets/icon.png")))
        self.json_file_handler = json_file_handler
        self.resize(1136, 568)
        self.selected_row = 0
        self.selected_col = 0

        self.table = QTableWidget()
        self.table.setColumnCount(22)
        self.table.setRowCount(33)  # Увеличено с 18 до 33 (3 заголовка + 30 строк данных)

        headers = ["", "", "без протравливания", "", "", "", "15 с", "", "", "", "30 с", "", "", "", "45 с", "", "", "",
                   "60 с",
                   "", "", ""]
        sub_headers = ["", "", "вестибулярная поверхность", "", "пришеечная область", "", "вестибулярная поверхность",
                       "", "пришеечная область", "", "вестибулярная поверхность", "", "пришеечная область", "",
                       "вестибулярная поверхность",
                       "", "пришеечная область", "", "вестибулярная поверхность", "", "пришеечная область", ""]
        sub_sub_headers = ["", "", "слабая", "сильная", "слабая", "сильная", "слабая", "сильная", "слабая", "сильная",
                           "слабая", "сильная", "слабая", "сильная", "слабая", "сильная",
                           "слабая", "сильная", "слабая", "сильная", "слабая", "сильная", "слабая", "сильная"]

        for row, data in enumerate([headers, sub_headers, sub_sub_headers]):
            for col, text in enumerate(data):
                self.table.setItem(row, col, QTableWidgetItem(text))

        self.table.setSpan(0, 0, 3, 2)
        for i in range(2, 20, 4):
            self.table.setSpan(0, i, 1, 4)
        for i in range(2, 22, 2):
            self.table.setSpan(1, i, 1, 2)

        # Расширенный список образцов 41-50
        samples = ["41", "", "", "42", "", "", "43", "", "", "44", "", "", "45", "", "",
                   "46", "", "", "47", "", "", "48", "", "", "49", "", "", "50", "", ""]
        time_mss = ["2", "5", "10", "2", "5", "10", "2", "5", "10", "2", "5", "10", "2", "5", "10",
                    "2", "5", "10", "2", "5", "10", "2", "5", "10", "2", "5", "10", "2", "5", "10"]

        for row, (sample, time_ms) in enumerate(zip(samples, time_mss), start=3):
            self.table.setItem(row, 0, QTableWidgetItem(sample))
            self.table.setItem(row, 1, QTableWidgetItem(time_ms))

        # Обновленные диапазоны для объединения ячеек образцов
        for i in range(3, 33, 3):  # Изменено с range(3, 16, 3) до range(3, 33, 3)
            self.table.setSpan(i, 0, 3, 1)

        for row in range(3, 33):  # Изменено с range(3, 18) до range(3, 33)
            for col in range(2, 22):
                sample, time_ms, type_, type_2, subtype = get_param_coil(row, col)
                filename = self.json_file_handler.get_filename(sample, time_ms, type_, type_2, subtype)
                if filename:
                    self.table.setItem(row, col, QTableWidgetItem(filename))

        for row in range(self.table.rowCount()):
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                if item:
                    item.setFlags(Qt.ItemIsEnabled)
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.table.setItem(row, col, item)

        self.table.cellClicked.connect(self.cell_selected)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        self.table.cellEntered.connect(self.highlight_intersection)
        self.table.setMouseTracking(True)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setVisible(False)

        # Обновленный список для выделения образцов жирным шрифтом
        make_bold(self.table, [(3, 0), (6, 0), (9, 0), (12, 0), (15, 0), (18, 0), (21, 0), (24, 0), (27, 0), (30, 0)])

        # Применяем форматирование и цветовое выделение групп образцов
        self.apply_table_formatting()

        for row in range(self.table.rowCount()):
            self.table.setRowHeight(row, 35)  # Увеличена высота строк для лучшей читаемости

        # Настройка ширины столбцов
        self.setup_column_widths()

        layout = QVBoxLayout()
        layout.addWidget(self.table)
        self.setLayout(layout)

    def apply_table_formatting(self):
        """Применяет цветовое форматирование для групп образцов"""

        # Цвета для чередования групп образцов
        group_colors = [
            QColor(240, 248, 255),  # Alice Blue - светло-голубой
            QColor(245, 255, 250),  # Mint Cream - светло-зеленый
            QColor(255, 248, 240),  # Orange - светло-оранжевый
            QColor(248, 240, 255),  # Lavender - светло-фиолетовый
            QColor(255, 240, 245),  # Lavender Blush - светло-розовый
            QColor(240, 255, 240),  # Honeydew - светло-зеленый
            QColor(255, 255, 240),  # Ivory - светло-желтый
            QColor(240, 255, 255),  # Azure - светло-голубой
            QColor(255, 240, 240),  # Misty Rose - светло-розовый
            QColor(248, 248, 255),  # Ghost White - почти белый
        ]

        # Применяем цвета к группам образцов (каждые 3 строки)
        for sample_group in range(10):  # 10 образцов (41-50)
            start_row = 3 + sample_group * 3
            end_row = start_row + 3
            color = group_colors[sample_group % len(group_colors)]

            for row in range(start_row, min(end_row, self.table.rowCount())):
                for col in range(self.table.columnCount()):
                    item = self.table.item(row, col)
                    if item:
                        item.setBackground(QBrush(color))

    def setup_column_widths(self):
        """Настраивает ширину столбцов по содержимому"""

        # Сначала подгоняем размеры по содержимому
        self.table.resizeColumnsToContents()
        self.table.resizeRowsToContents()

        # Устанавливаем минимальную ширину для столбцов
        column_min_widths = {
            0: 80,  # Sample - номер образца
            1: 60,  # Time - время
        }

        # Для столбцов с данными файлов (2-21) устанавливаем единую ширину
        data_column_width = 80

        for col in range(self.table.columnCount()):
            if col in column_min_widths:
                current_width = self.table.columnWidth(col)
                min_width = column_min_widths[col]
                self.table.setColumnWidth(col, max(current_width, min_width))
            elif col >= 2:  # Столбцы с данными файлов
                self.table.setColumnWidth(col, data_column_width)

    def add_sample_separators(self):
        """Добавляет визуальные разделители между группами образцов"""
        # Применяем стили для выделения границ между группами
        style_sheet = """
            QTableWidget {
                gridline-color: #CCCCCC;
                selection-background-color: #3399FF;
            }
            QTableWidget::item {
                border: 1px solid #E0E0E0;
                padding: 4px;
            }
            QTableWidget::item:selected {
                background-color: #3399FF;
                color: white;
            }
        """
        self.table.setStyleSheet(style_sheet)

    def highlight_intersection(self, row, col):
        self.selected_row = row
        self.selected_col = col
        normal_font = QFont()
        normal_font.setBold(False)

        for r in range(self.table.rowCount()):
            for c in range(self.table.columnCount()):
                item = self.table.item(r, c)
                if item:
                    item.setFont(normal_font)
                    item.setBackground(QBrush(Qt.white))
                    item.setForeground(QBrush(Qt.black))

        if row < 3 or col < 2:
            return

        column_groups = {range(2, 6): 2, range(6, 10): 6, range(10, 14): 10,
                         range(14, 18): 14, range(18, 22): 18}

        header_col = next((v for k, v in column_groups.items() if col in k), None)
        if header_col is not None:
            make_bold(self.table, [(0, header_col)])
            item = self.table.item(0, header_col)
            if item is not None:
                item.setBackground(QBrush(QColor(173, 216, 230)))
                item.setForeground(QBrush(Qt.black))

        subheader_col = col if col % 2 == 0 else col - 1
        make_bold(self.table, [(1, subheader_col), (2, col)])
        for i in (1, 2):
            item = self.table.item(i, subheader_col if i == 1 else col)
            if item is not None:
                item.setBackground(QBrush(QColor(173, 216, 230)))
                item.setForeground(QBrush(Qt.black))

        # Обновленные диапазоны для выделения строк образцов
        row_groups = {range(3, 6): 3, range(6, 9): 6, range(9, 12): 9, range(12, 15): 12, range(15, 18): 15,
                      range(18, 21): 18, range(21, 24): 21, range(24, 27): 24, range(27, 30): 27, range(30, 33): 30}

        make_bold(self.table, [(row, 1)])

        header_row = next((v for k, v in row_groups.items() if row in k), None)
        if header_row is not None:
            make_bold(self.table, [(header_row, 0)])
            item = self.table.item(header_row, 0)
            if item is not None:
                item.setBackground(QBrush(QColor(173, 216, 230)))
                item.setForeground(QBrush(Qt.black))

        for c in range(col + 1):
            item = self.table.item(row, c)
            if item:
                item.setBackground(QBrush(QColor(173, 216, 230)))
                item.setForeground(QBrush(Qt.black))

        for r in range(row + 1):
            item = self.table.item(r, col)
            if item:
                item.setBackground(QBrush(QColor(173, 216, 230)))
                item.setForeground(QBrush(Qt.black))

        item = self.table.item(row, col)
        if item:
            item.setFont(normal_font)
            item.setBackground(QBrush(Qt.yellow))
        self.table.repaint()
        self.table.viewport().update()

    def cell_selected(self, row, col):
        self.selected_row = row
        self.selected_col = col

    def show_context_menu(self, pos: QPoint):
        menu = QMenu(self)
        open_action = QAction("Открыть", self)
        edit_action = QAction("Изменить", self)
        open_action.triggered.connect(self.open_graph)
        edit_action.triggered.connect(self.edit_cell)
        menu.addAction(open_action)
        menu.addAction(edit_action)
        menu.exec_(self.table.viewport().mapToGlobal(pos))

    def edit_cell(self):
        item = self.table.item(self.selected_row, self.selected_col)
        if item:
            item.setFlags(item.flags() | Qt.ItemIsEditable)
            self.table.editItem(item)
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            self.table.itemChanged.connect(self.save_to_json)

    def save_to_json(self, item):
        if item.row() == self.selected_row and item.column() == self.selected_col:
            new_value = item.text()
            sample, time_ms, type_, type_2, subtype = get_param_coil(self.selected_row, self.selected_col)
            self.json_file_handler.update_filename(sample, time_ms, type_, type_2, subtype, new_value)
            self.table.itemChanged.disconnect(self.save_to_json)

    def open_graph(self):
        item = self.table.item(self.selected_row, self.selected_col)
        if item:
            self.filename = item.text() + ".txt"
            filepath = os.path.join("library/", self.filename)
            self.start_processing(get_resource_path(filepath))