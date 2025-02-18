import json
import sys

from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QFont, QColor, QBrush
from PyQt5.QtWidgets import QApplication, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget, QAction, QMenu

from GUI.table_utils import make_bold, get_param_coil


class TableApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Таблица файлов")

        self.resize(1000, 600)
        self.selected_row = 0
        self.selected_col = 0
        self.json_path = "table.json"
        with open(self.json_path, "r", encoding="utf-8") as file:
            self.data = json.load(file)

        self.table = QTableWidget()
        self.table.setColumnCount(22)
        self.table.setRowCount(18)

        headers = ["", "", "без провр", "", "", "", "15 с", "", "", "", "30 с", "", "", "", "45 с", "", "", "", "60 с",
                   "", "", ""]
        sub_headers = ["", "", "вест s", "", "приш", "", "вест s", "", "приш", "", "вест s", "", "приш", "", "вест s",
                       "", "приш", "", "вест s", "", "приш", ""]
        sub_sub_headers = ["", "", "сл.", "F", "сл.", "F", "сл.", "F", "сл.", "F", "сл.", "F", "сл.", "F", "сл.", "F",
                           "сл.", "F", "сл.", "F", "сл.", "F", "сл.", "F"]

        for row, data in enumerate([headers, sub_headers, sub_sub_headers]):
            for col, text in enumerate(data):
                self.table.setItem(row, col, QTableWidgetItem(text))

        self.table.setSpan(0, 0, 3, 2)
        for i in range(2, 20, 4):
            self.table.setSpan(0, i, 1, 4)
        for i in range(2, 22, 2):
            self.table.setSpan(1, i, 1, 2)

        samples = ["41", "", "", "42", "", "", "43", "", "", "44", "", "", "45", "", ""]
        time_mss = ["2", "5", "10", "2", "5", "10", "2", "5", "10", "2", "5", "10", "2", "5", "10"]

        for row, (sample, time_ms) in enumerate(zip(samples, time_mss), start=3):
            self.table.setItem(row, 0, QTableWidgetItem(sample))
            self.table.setItem(row, 1, QTableWidgetItem(time_ms))

        for i in range(3, 16, 3):
            self.table.setSpan(i, 0, 3, 1)

        for row in range(3, 18):
            for col in range(2, 22):
                sample, time_ms, type_, type_2, subtype = get_param_coil(row, col)
                filename = self.get_filename(sample, time_ms, type_, type_2, subtype)
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

        make_bold(self.table, [(3, 0), (6, 0), (9, 0), (12, 0), (15, 0)])
        for row in range(self.table.rowCount()):
            self.table.setRowHeight(row, 30)
        for col in range(self.table.columnCount()):
            self.table.setColumnWidth(col, 50)
        self.table.resizeColumnsToContents()
        self.table.resizeRowsToContents()
        layout = QVBoxLayout()
        layout.addWidget(self.table)
        self.setLayout(layout)

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

        row_groups = {range(3, 5): 3, range(6, 8): 6, range(9, 11): 9,
                      range(12, 14): 12, range(15, 17): 15}

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

    def open_graph(self):
        item = self.table.item(self.selected_row, self.selected_col)
        if item:
            filename = item.text() + ".txt"
            print(filename)

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

            for entry in self.data:
                if (entry["sample"] == sample and entry["time_ms"] == time_ms and
                        entry["type"] == type_ and entry["type_2"] == type_2 and entry["subtype"] == subtype):
                    entry["filename"] = new_value + ".txt"
                    break

            with open(self.json_path, "w", encoding="utf-8") as file:
                json.dump(self.data, file, indent=4, ensure_ascii=False)
            self.table.itemChanged.disconnect(self.save_to_json)

    def get_filename(self, sample, time_ms, type_, type_2, subtype):
        for item in self.data:
            if (item["sample"] == sample and item["time_ms"] == time_ms and
                    item["type"] == type_ and item["type_2"] == type_2 and item["subtype"] == subtype):
                return item["filename"][0:-4]
        return None


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TableApp()
    window.show()
    sys.exit(app.exec_())
