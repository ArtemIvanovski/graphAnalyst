import numpy as np
import pandas as pd
import pyqtgraph as pg
import pyqtgraph.exporters
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QIcon
from PyQt5.QtGui import QPainter
from PyQt5.QtPrintSupport import QPrinter
from PyQt5.QtWidgets import QColorDialog
from PyQt5.QtWidgets import (
    QMainWindow, QVBoxLayout, QWidget, QToolBar, QAction, QMenu, QCheckBox, QSlider, QLabel,
    QHBoxLayout, QWidgetAction, QFileDialog, QMessageBox
)

from core.settings_handler import get_resource_path


class GraphWindow(QMainWindow):
    def __init__(self, metadata, data_frame, filename):
        super().__init__()
        self.data_frame = data_frame
        self.metadata = metadata
        self.line_color = "b"
        self.setWindowTitle(f"Graph Viewer {filename}")
        self.showMaximized()
        self.setWindowIcon(QIcon(get_resource_path("assets/icon.png")))

        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)

        self.layout = QVBoxLayout()
        self.main_widget.setLayout(self.layout)

        self.toolbar = QToolBar("Graph Controls")
        self.toolbar.setFixedHeight(64)
        self.addToolBar(self.toolbar)
        self.toolbar.setMovable(False)
        self.toolbar.setStyleSheet("""
                QToolBar {
                    background: #e0e0e0;
                    padding: 5px;
                    spacing: 10px;  
                }
                QToolButton {
                    border: 1px solid #ccc;  
                    padding: 5px;
                    background: white;
                    border-radius: 4px;  
                }
                QToolButton:hover {
                    background: #dcdcdc;
                }
                QToolButton:pressed {
                    background: #bcbcbc;
                }
            """)
        reload_action = QAction(QIcon(get_resource_path("assets/iconRefresh.png")), "Перезагрузить", self)
        reload_action.triggered.connect(self.reload_graph)
        self.toolbar.addAction(reload_action)

        self.transform_menu = QMenu(self)
        transform_action = QAction(QIcon(get_resource_path("assets/iconTransform.png")), "Трансформация", self)
        self.toolbar.addAction(transform_action)
        transform_action.triggered.connect(lambda: self.transform_menu.exec_(self.toolbar.mapToGlobal(QPoint(60, 58))))

        self.checkboxes = {}
        transform_options = ["Power Spectrum (FFT)", "Log X", "Log Y", "dy/dx"]
        for option in transform_options:
            checkbox = QCheckBox(option, self)
            checkbox.stateChanged.connect(self.update_graph)
            self.checkboxes[option] = checkbox
            action = QWidgetAction(self)
            action.setDefaultWidget(checkbox)
            self.transform_menu.addAction(action)

        self.grid_menu = QMenu(self)
        grid_action = QAction(QIcon(get_resource_path("assets/iconGrid.png")), "Сетка", self)
        self.toolbar.addAction(grid_action)
        grid_action.triggered.connect(lambda: self.grid_menu.exec_(self.toolbar.mapToGlobal(QPoint(116, 58))))

        self.show_x_grid = QCheckBox("Show X Grid", self)
        self.show_x_grid.setChecked(True)
        self.show_x_grid.stateChanged.connect(self.update_graph)
        action_x_grid = QWidgetAction(self)
        action_x_grid.setDefaultWidget(self.show_x_grid)
        self.grid_menu.addAction(action_x_grid)

        self.show_y_grid = QCheckBox("Show Y Grid", self)
        self.show_y_grid.setChecked(True)
        self.show_y_grid.stateChanged.connect(self.update_graph)
        action_y_grid = QWidgetAction(self)
        action_y_grid.setDefaultWidget(self.show_y_grid)
        self.grid_menu.addAction(action_y_grid)

        opacity_label = QLabel("Opacity")
        self.opacity_slider = QSlider(Qt.Horizontal, self)
        self.opacity_slider.setMinimum(10)
        self.opacity_slider.setMaximum(100)
        self.opacity_slider.setValue(50)
        self.opacity_slider.setTickInterval(10)
        self.opacity_slider.setTickPosition(QSlider.TicksBelow)
        self.opacity_slider.valueChanged.connect(self.update_graph)

        slider_layout = QHBoxLayout()
        slider_layout.addWidget(opacity_label)
        slider_layout.addWidget(self.opacity_slider)
        slider_widget = QWidget()
        slider_widget.setLayout(slider_layout)

        action_opacity = QWidgetAction(self)
        action_opacity.setDefaultWidget(slider_widget)
        self.grid_menu.addAction(action_opacity)

        y_axis_action = QAction(QIcon(get_resource_path("assets/iconYAxis.png")), "Ось Y", self)
        self.toolbar.addAction(y_axis_action)
        self.y_axis_menu = QMenu(self)
        y_axis_action.triggered.connect(lambda: self.y_axis_menu.exec_(self.toolbar.mapToGlobal(QPoint(172, 58))))

        self.y_invert_axis = QCheckBox("Invert Axis", self)
        self.y_invert_axis.stateChanged.connect(
            lambda: self.plot_widget.getPlotItem().invertY(self.y_invert_axis.isChecked()))
        action_y_invert = QWidgetAction(self)
        action_y_invert.setDefaultWidget(self.y_invert_axis)
        self.y_axis_menu.addAction(action_y_invert)

        self.y_mouse_enabled = QCheckBox("Mouse Enabled", self)
        self.y_mouse_enabled.setChecked(True)
        self.y_mouse_enabled.stateChanged.connect(
            lambda: self.plot_widget.setMouseEnabled(y=self.y_mouse_enabled.isChecked()))
        action_y_mouse = QWidgetAction(self)
        action_y_mouse.setDefaultWidget(self.y_mouse_enabled)
        self.y_axis_menu.addAction(action_y_mouse)

        x_axis_action = QAction(QIcon(get_resource_path("assets/iconXAxis.png")), "Ось X", self)
        self.toolbar.addAction(x_axis_action)
        self.x_axis_menu = QMenu(self)
        x_axis_action.triggered.connect(lambda: self.x_axis_menu.exec_(self.toolbar.mapToGlobal(QPoint(228, 58))))

        self.x_invert_axis = QCheckBox("Invert Axis", self)
        self.x_invert_axis.stateChanged.connect(
            lambda: self.plot_widget.getPlotItem().invertX(self.x_invert_axis.isChecked()))
        action_x_invert = QWidgetAction(self)
        action_x_invert.setDefaultWidget(self.x_invert_axis)
        self.x_axis_menu.addAction(action_x_invert)

        self.x_mouse_enabled = QCheckBox("Mouse Enabled", self)
        self.x_mouse_enabled.setChecked(True)
        self.x_mouse_enabled.stateChanged.connect(
            lambda: self.plot_widget.setMouseEnabled(x=self.x_mouse_enabled.isChecked()))
        action_x_mouse = QWidgetAction(self)
        action_x_mouse.setDefaultWidget(self.x_mouse_enabled)
        self.x_axis_menu.addAction(action_x_mouse)

        info_action = QAction(QIcon(get_resource_path("assets/iconInfo.png")), "Info", self)
        self.toolbar.addAction(info_action)
        info_action.triggered.connect(self.show_metadata_info)

        color_action = QAction(QIcon(get_resource_path("assets/iconTrend.png")), "Изменить цвет линии", self)
        self.toolbar.addAction(color_action)
        color_action.triggered.connect(self.change_line_color)

        export_action = QAction(QIcon(get_resource_path("assets/iconExport.png")), "Экспорт", self)
        self.toolbar.addAction(export_action)
        export_action.triggered.connect(self.export_graph)

        self.plot_widget = self.create_plot()
        self.layout.addWidget(self.plot_widget)

    def create_plot(self):
        plot_widget = pg.PlotWidget()
        plot_widget.setBackground("w")
        plot_item = plot_widget.getPlotItem()
        plot_item.setMenuEnabled(False)
        plot_widget.showGrid(x=True, y=True, alpha=0.5)

        self.x_data = self.data_frame["Index"].values
        self.y_data = self.data_frame["Voltage (mV)"].values
        self.plot = plot_widget.plot(self.x_data, self.y_data, pen=pg.mkPen(color="b", width=2), name="Voltage (mV)")

        plot_widget.setLabel("left", "Voltage (mV)", **{"color": "blue", "font-size": "14pt"})
        plot_widget.setLabel("bottom", "Time (µs)", **{"color": "blue", "font-size": "14pt"})

        plot_widget.setMouseEnabled(x=True, y=True)
        plot_widget.addLegend()

        return plot_widget

    def update_graph(self):
        log_x = self.checkboxes["Log X"].isChecked()
        log_y = self.checkboxes["Log Y"].isChecked()
        dy_dx = self.checkboxes["dy/dx"].isChecked()
        fft = self.checkboxes["Power Spectrum (FFT)"].isChecked()

        x = self.x_data
        y = self.y_data

        if dy_dx:
            x = x[1:]
            y = np.diff(y)

        if fft:
            y = np.abs(np.fft.rfft(y))
            x = np.fft.rfftfreq(len(self.x_data), d=(self.x_data[1] - self.x_data[0]))

        if len(x) != len(y):
            return

        if log_x:
            x = np.log10(np.clip(x, 1e-10, None))

        if log_y:
            y = np.log10(np.clip(y, 1e-10, None))

        self.plot.setData(x, y)
        self.plot_widget.setLogMode(x=log_x, y=log_y)

        alpha = self.opacity_slider.value() / 100.0
        self.plot_widget.showGrid(x=self.show_x_grid.isChecked(), y=self.show_y_grid.isChecked(), alpha=alpha)

    def reload_graph(self):
        self.layout.removeWidget(self.plot_widget)
        self.plot_widget.deleteLater()
        self.plot_widget = self.create_plot()
        self.layout.addWidget(self.plot_widget)

    def export_graph(self):
        options = QFileDialog.Options()
        file_path, file_type = QFileDialog.getSaveFileName(
            self, "Экспортировать график", "",
            "Изображение PNG (*.png);;Изображение JPG (*.jpg);;CSV файл (*.csv);;Excel файл (*.xlsx);;PDF файл (*.pdf)",
            options=options
        )

        if file_path:
            if file_type.startswith("Изображение"):
                exporter = pyqtgraph.exporters.ImageExporter(self.plot_widget.plotItem)
                exporter.export(file_path)
                QMessageBox.information(self, "Экспорт завершен", f"График сохранен как {file_path}")

            elif file_type.startswith("CSV"):
                np.savetxt(file_path, np.column_stack((self.x_data, self.y_data)), delimiter=",",
                           header="Index,Voltage (mV)", comments="")
                QMessageBox.information(self, "Экспорт завершен", f"График сохранен как {file_path}")

            elif file_type.startswith("Excel"):
                self.save_as_excel(file_path)

            elif file_type.startswith("PDF"):
                self.save_as_pdf(file_path)

    def save_as_pdf(self, file_path):
        printer = QPrinter()
        printer.setOutputFormat(QPrinter.PdfFormat)
        printer.setOutputFileName(file_path)
        printer.setOrientation(QPrinter.Landscape)
        printer.setResolution(300)
        printer.setFullPage(True)
        painter = QPainter(printer)
        self.plot_widget.render(painter)
        painter.end()

        QMessageBox.information(self, "Экспорт завершен", f"График сохранен как {file_path}")

    def save_as_excel(self, file_path):
        df = pd.DataFrame({"X (Time)": self.x_data, "Y (Voltage)": self.y_data})
        df.to_excel(file_path, index=False, sheet_name="Graph Data")

        QMessageBox.information(self, "Экспорт завершен", f"График сохранен как {file_path}")

    def show_metadata_info(self):
        info_text = "\n".join(f"{key}: {value}" for key, value in self.metadata.items())
        QMessageBox.information(self, "Graph Metadata", info_text)

    def change_line_color(self):
        color_dialog = QColorDialog(self)
        color = color_dialog.getColor()

        if color.isValid():
            self.line_color = color.name()
            self.plot.setPen(pg.mkPen(color=self.line_color, width=2))

            self.plot_widget.setLabel("left", "Voltage (mV)", **{"color": self.line_color, "font-size": "14pt"})
            self.plot_widget.setLabel("bottom", "Time (µs)", **{"color": self.line_color, "font-size": "14pt"})


