from PyQt5.QtGui import QFont


def make_bold(table, cells):
    bold_font = QFont()
    bold_font.setBold(True)

    for row, col in cells:
        item = table.item(row, col)
        if item:
            item.setFont(bold_font)


def get_param_coil(row, col):
    subtype = "слабая" if col % 2 == 0 else "сильная"

    type_2 = "вестибулярная поверхность" if ((col - 2) // 2) % 2 == 0 else "пришеечная область"

    type_dict = {range(2, 6): "без протравливания", range(6, 10): "15 с", range(10, 14): "30 с",
                 range(14, 18): "45 с", range(18, 22): "60 с"}
    type_ = next((v for k, v in type_dict.items() if col in k), None)

    time_ms = [2, 5, 10][row % 3]

    sample = int(41 + (row - 3) // 3)
    return sample, time_ms, type_, type_2, subtype
