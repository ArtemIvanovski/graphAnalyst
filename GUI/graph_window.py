import pyqtgraph as pg
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QWidget

from GUI.top_bar_with_icons import create_top_bar_with_icons
from core.data_frame_utils import multiply_data


class GraphWindow(QMainWindow):
    def __init__(self, metadata, data_frame, main_window, app):
        super().__init__()
        self.app = app

        time_interval = metadata.get("Time interval", "")
        if not time_interval:
            raise ValueError("Метаданные не содержат 'Time interval'.")

        self.data_frame = multiply_data(data_frame, time_interval)
        self.metadata = metadata
        self.main_window = main_window

        self.setWindowTitle("Graph Viewer")
        self.setStyleSheet("background-color: #f3f3f3;")
        self.setWindowIcon(QIcon("assets/icon.png"))

        self.showMaximized()

        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)

        self.layout = QVBoxLayout()
        self.main_widget.setLayout(self.layout)

        white_strip, grey_strip, _, _ = create_top_bar_with_icons(
            self, None, self.return_to_main, app, None, metadata
        )
        self.layout.addWidget(white_strip)
        self.layout.addWidget(grey_strip)

        self.plot_widget = self.create_plot()
        self.layout.addWidget(self.plot_widget)

    def create_plot(self):
        plot_widget = pg.PlotWidget()
        plot_widget.setBackground("w")
        plot_widget.showGrid(x=True, y=True, alpha=0.5)

        x = self.data_frame["Index"].values
        y = self.data_frame["Voltage (mV)"].values
        plot_widget.plot(x, y, pen=pg.mkPen(color="b", width=2), name="Voltage (mV)")

        plot_widget.setLabel("left", "Voltage (mV)", **{"color": "blue", "font-size": "14pt"})
        plot_widget.setLabel("bottom", "Time (µs)", **{"color": "blue", "font-size": "14pt"})

        plot_widget.setMouseEnabled(x=True, y=True)
        plot_widget.addLegend()

        return plot_widget

    def return_to_main(self):
        self.close()
        self.main_window.show()

    def closeEvent(self, event):
        self.main_window.show()
        event.accept()
