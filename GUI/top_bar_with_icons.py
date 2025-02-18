from PyQt5.QtCore import QSize
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QPushButton


def create_button(text, icon_path, icon_size=QSize(100, 100)):
    button = QPushButton()
    button.setStyleSheet("""
        QPushButton {
            background-color: #afb2b7;
        }
    """)
    button.setFixedSize(QSize(400, 200))
    button.setIconSize(icon_size)
    button.setIcon(QIcon(icon_path))
    button.setText(text)
    return button
