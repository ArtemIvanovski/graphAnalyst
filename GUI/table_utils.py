from PyQt5.QtGui import QFont


def make_bold(table, cells):
    bold_font = QFont()
    bold_font.setBold(True)

    for row, col in cells:
        item = table.item(row, col)
        if item:
            item.setFont(bold_font)
