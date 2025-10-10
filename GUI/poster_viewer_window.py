import os
import shutil
from PyQt5.QtWidgets import (QMainWindow, QVBoxLayout, QWidget, QLabel,
                             QFileDialog, QMessageBox, QScrollArea, QShortcut)
from PyQt5.QtGui import QPixmap, QIcon, QWheelEvent, QKeySequence, QCursor
from PyQt5.QtCore import Qt, QPoint
from core.settings_handler import get_resource_path


class ZoomableLabel(QLabel):
    def __init__(self, scroll_area):
        super().__init__()
        self.setAlignment(Qt.AlignCenter)
        self.setScaledContents(False)
        self.scale_factor = 1.0
        self.original_pixmap = None
        self.scroll_area = scroll_area
        self.dragging = False
        self.last_pan_point = QPoint()

    def setPixmap(self, pixmap):
        self.original_pixmap = pixmap
        self.scale_factor = 1.0
        super().setPixmap(pixmap)

    def wheelEvent(self, event: QWheelEvent):
        if self.original_pixmap is None:
            return

        cursor_pos = event.pos()
        h_scrollbar = self.scroll_area.horizontalScrollBar()
        v_scrollbar = self.scroll_area.verticalScrollBar()
        old_h_value = h_scrollbar.value()
        old_v_value = v_scrollbar.value()

        widget_size = self.size()
        if widget_size.width() > 0 and widget_size.height() > 0:
            rel_x = cursor_pos.x() / widget_size.width()
            rel_y = cursor_pos.y() / widget_size.height()
        else:
            rel_x = 0.5
            rel_y = 0.5

        angle_delta = event.angleDelta().y()
        zoom_in = angle_delta > 0
        old_scale = self.scale_factor
        zoom_factor = 1.15 if zoom_in else 0.87
        self.scale_factor *= zoom_factor
        self.scale_factor = max(0.1, min(self.scale_factor, 10.0))

        new_width = int(self.original_pixmap.width() * self.scale_factor)
        new_height = int(self.original_pixmap.height() * self.scale_factor)

        scaled_pixmap = self.original_pixmap.scaled(
            new_width, new_height,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )

        super().setPixmap(scaled_pixmap)
        self.resize(new_width, new_height)

        scale_change = self.scale_factor / old_scale
        viewport_center_x = self.scroll_area.viewport().width() / 2
        viewport_center_y = self.scroll_area.viewport().height() / 2
        cursor_in_viewport = self.scroll_area.widget().mapFromParent(cursor_pos)
        offset_x = cursor_in_viewport.x() - viewport_center_x
        offset_y = cursor_in_viewport.y() - viewport_center_y
        new_offset_x = offset_x * scale_change
        new_offset_y = offset_y * scale_change
        new_h_value = old_h_value + (new_offset_x - offset_x)
        new_v_value = old_v_value + (new_offset_y - offset_y)

        h_scrollbar.setValue(int(new_h_value))
        v_scrollbar.setValue(int(new_v_value))
        event.accept()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.last_pan_point = event.pos()
            self.setCursor(QCursor(Qt.ClosedHandCursor))
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.dragging and event.buttons() == Qt.LeftButton:
            delta = event.pos() - self.last_pan_point
            self.last_pan_point = event.pos()

            h_scrollbar = self.scroll_area.horizontalScrollBar()
            v_scrollbar = self.scroll_area.verticalScrollBar()

            h_scrollbar.setValue(h_scrollbar.value() - delta.x())
            v_scrollbar.setValue(v_scrollbar.value() - delta.y())
        else:
            self.setCursor(QCursor(Qt.OpenHandCursor))
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = False
            self.setCursor(QCursor(Qt.OpenHandCursor))
        super().mouseReleaseEvent(event)

    def enterEvent(self, event):
        self.setCursor(QCursor(Qt.OpenHandCursor))
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.setCursor(QCursor(Qt.ArrowCursor))
        super().leaveEvent(event)


class PosterViewerWindow(QMainWindow):
    def __init__(self, poster_path, temp_folder, selected_params=None, parent=None):
        super().__init__(parent)
        self.poster_path = poster_path
        self.temp_folder = temp_folder
        self.selected_params = selected_params or {}

        self.setWindowTitle("Просмотр плаката")
        self.setWindowIcon(QIcon(get_resource_path("assets/icon.png")))
        self.showMaximized()

        self.init_ui()
        self.setup_shortcuts()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setAlignment(Qt.AlignCenter)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.image_label = ZoomableLabel(self.scroll_area)
        self.load_poster()

        self.scroll_area.setWidget(self.image_label)
        layout.addWidget(self.scroll_area)
        central_widget.setLayout(layout)

    def setup_shortcuts(self):
        save_shortcut = QShortcut(QKeySequence.Save, self)
        save_shortcut.activated.connect(self.save_poster)

        close_shortcut = QShortcut(QKeySequence(Qt.Key_Escape), self)
        close_shortcut.activated.connect(self.close)

    def load_poster(self):
        try:
            pixmap = QPixmap(self.poster_path)
            if not pixmap.isNull():
                self.image_label.setPixmap(pixmap)
                self.image_label.resize(pixmap.size())
            else:
                self.image_label.setText("Ошибка загрузки изображения")
        except Exception as e:
            self.image_label.setText("Ошибка загрузки изображения")

    def save_poster(self):
        try:
            if self.selected_params:
                sample = self.selected_params.get('sample', 'unknown')
                time_ms = self.selected_params.get('time_ms', 'unknown')
                localization = self.selected_params.get('localization', 'unknown')
                intensity = self.selected_params.get('intensity', 'unknown')

                sample_clean = str(sample).replace(' ', '_').replace('/', '_')
                time_clean = str(time_ms).replace(' ', '_').replace('/', '_')
                localization_clean = str(localization).replace(' ', '_').replace('/', '_')
                intensity_clean = str(intensity).replace(' ', '_').replace('/', '_')

                default_filename = f"плакат_образец_{sample_clean}_{time_clean}мс_{localization_clean}_{intensity_clean}.png"
            else:
                default_filename = "spectrograms_poster.png"

            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Сохранить плакат",
                default_filename,
                "PNG Images (*.png);;JPEG Images (*.jpg);;PDF Files (*.pdf);;All Files (*)"
            )

            if file_path:
                shutil.copy2(self.poster_path, file_path)
                QMessageBox.information(
                    self,
                    "Сохранение завершено",
                    f"Плакат успешно сохранен:\n{file_path}"
                )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Ошибка сохранения",
                f"Не удалось сохранить плакат:\n{str(e)}"
            )

    def cleanup_temp_files(self):
        try:
            if os.path.exists(self.temp_folder):
                shutil.rmtree(self.temp_folder)
        except Exception as e:
            pass

    def closeEvent(self, event):
        self.cleanup_temp_files()
        event.accept()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_F11:
            if self.isFullScreen():
                self.showMaximized()
            else:
                self.showFullScreen()
        else:
            super().keyPressEvent(event)