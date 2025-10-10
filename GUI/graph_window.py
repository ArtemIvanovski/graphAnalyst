import numpy as np
import pandas as pd
import pyqtgraph as pg
import pyqtgraph.exporters
from PyQt5.QtCore import Qt, QPoint, QRectF
from PyQt5.QtGui import QIcon
from PyQt5.QtGui import QPainter
from PyQt5.QtPrintSupport import QPrinter
from PyQt5.QtWidgets import QColorDialog, QDialog
from PyQt5.QtWidgets import (
    QMainWindow, QVBoxLayout, QWidget, QToolBar, QAction, QMenu, QCheckBox, QSlider, QLabel,
    QHBoxLayout, QWidgetAction, QFileDialog, QMessageBox
)
from pyqtgraph import ImageItem, ColorBarItem, GraphicsLayoutWidget
from scipy import signal
from scipy.signal import stft

from GUI.filter_window import FilterWindow
from core.settings_handler import get_resource_path


class GraphWindow(QMainWindow):
    def __init__(self, metadata, data_frame, filename):
        super().__init__()
        self.plot = None
        self.spectrogram_data = None
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
        self.add_spectrogram_button()
        self.add_filter_button()
        self.plot_widget = self.create_plot()
        self.layout.addWidget(self.plot_widget)

    def add_filter_button(self):
        """Добавляет кнопку фильтрации сигнала"""
        filter_action = QAction(QIcon(get_resource_path("assets/iconFilter.png")),
                                "Фильтрация", self)
        filter_action.triggered.connect(self.open_filter_dialog)
        self.toolbar.addAction(filter_action)

    def open_filter_dialog(self):
        """Открывает диалог настройки фильтра"""
        dialog = FilterWindow(self)
        if dialog.exec_() == QDialog.Accepted:
            filter_type, params = dialog.get_filter_params()
            if filter_type and params:
                self.apply_advanced_filter(filter_type, params)

    def update_plot_after_filter(self):
        """Обновляет график после применения фильтра"""
        if isinstance(self.plot_widget, GraphicsLayoutWidget):
            self.reload_graph()
        else:
            self.plot.setData(self.x_data, self.y_data)

    def apply_advanced_filter(self, filter_type, params):
        """Применяет фильтр с расширенными параметрами"""
        try:
            if filter_type == "reset":
                self.y_data = self.data_frame["Voltage (mV)"].values.copy()
                self.update_plot_after_filter()
                QMessageBox.information(self, "Фильтрация", "Фильтры сброшены")
                return

            dt = self.dt
            fs = 1.0 / dt
            nyquist = fs / 2
            y_filtered = self.y_data.copy()

            if len(y_filtered) < 10:
                QMessageBox.warning(self, "Ошибка", "Недостаточно данных для фильтрации")
                return

            if filter_type == "bandpass":
                low_freq, high_freq, order = params

                # Проверки корректности параметров
                if high_freq <= low_freq:
                    QMessageBox.warning(self, "Ошибка", "Верхняя частота должна быть больше нижней")
                    return

                if high_freq >= nyquist:
                    high_freq = nyquist * 0.95

                if low_freq <= 0:
                    low_freq = 1

                low = low_freq / nyquist
                high = high_freq / nyquist

                if low >= 1.0 or high >= 1.0 or low <= 0 or high <= 0:
                    QMessageBox.warning(self, "Ошибка",
                                        f"Некорректные частоты: {low_freq}-{high_freq} Гц при fs={fs:.0f} Гц")
                    return

                b, a = signal.butter(order, [low, high], btype='band')
                y_filtered = signal.filtfilt(b, a, y_filtered)
                filter_info = f"Полосовой фильтр {low_freq}-{high_freq:.0f} Гц (порядок {order})"

            elif filter_type == "bandstop":
                low_freq, high_freq, order = params

                if high_freq <= low_freq:
                    QMessageBox.warning(self, "Ошибка", "Верхняя частота должна быть больше нижней")
                    return

                if high_freq >= nyquist:
                    high_freq = nyquist * 0.95

                if low_freq <= 0:
                    low_freq = 1

                low = low_freq / nyquist
                high = high_freq / nyquist

                if low >= 1.0 or high >= 1.0 or low <= 0 or high <= 0:
                    QMessageBox.warning(self, "Ошибка",
                                        f"Некорректные частоты: {low_freq}-{high_freq} Гц при fs={fs:.0f} Гц")
                    return

                b, a = signal.butter(order, [low, high], btype='bandstop')
                y_filtered = signal.filtfilt(b, a, y_filtered)
                filter_info = f"Полосовой режекторный фильтр {low_freq}-{high_freq:.0f} Гц (порядок {order})"

            elif filter_type == "notch":
                freq_to_remove, quality_factor = params

                if freq_to_remove <= 0 or freq_to_remove >= nyquist:
                    QMessageBox.warning(self, "Ошибка", f"Частота {freq_to_remove} Гц вне допустимого диапазона")
                    return

                if quality_factor <= 0:
                    quality_factor = 30

                b, a = signal.iirnotch(freq_to_remove, quality_factor, fs)
                y_filtered = signal.filtfilt(b, a, y_filtered)
                filter_info = f"Режекторный фильтр {freq_to_remove} Гц (Q={quality_factor})"

            elif filter_type == "highpass":
                cutoff_freq, order = params

                if cutoff_freq <= 0 or cutoff_freq >= nyquist:
                    QMessageBox.warning(self, "Ошибка", f"Частота среза {cutoff_freq} Гц вне допустимого диапазона")
                    return

                cutoff_normalized = cutoff_freq / nyquist

                if cutoff_normalized >= 1.0 or cutoff_normalized <= 0:
                    QMessageBox.warning(self, "Ошибка", "Некорректная нормализованная частота среза")
                    return

                b, a = signal.butter(order, cutoff_normalized, btype='high')
                y_filtered = signal.filtfilt(b, a, y_filtered)
                filter_info = f"ВЧ фильтр > {cutoff_freq} Гц (порядок {order})"

            elif filter_type == "lowpass":
                cutoff_freq, order = params

                if cutoff_freq <= 0 or cutoff_freq >= nyquist:
                    cutoff_freq = nyquist * 0.95

                cutoff_normalized = cutoff_freq / nyquist

                if cutoff_normalized >= 1.0 or cutoff_normalized <= 0:
                    QMessageBox.warning(self, "Ошибка", "Некорректная нормализованная частота среза")
                    return

                b, a = signal.butter(order, cutoff_normalized, btype='low')
                y_filtered = signal.filtfilt(b, a, y_filtered)
                filter_info = f"НЧ фильтр < {cutoff_freq:.0f} Гц (порядок {order})"

            else:
                QMessageBox.warning(self, "Ошибка", f"Неизвестный тип фильтра: {filter_type}")
                return

            if np.any(np.isnan(y_filtered)) or np.any(np.isinf(y_filtered)):
                QMessageBox.warning(self, "Ошибка", "Фильтрация привела к некорректным значениям")
                return

            self.y_data = y_filtered
            self.update_plot_after_filter()

            QMessageBox.information(self, "Фильтрация завершена",
                                    f"Применен {filter_info}\nЧастота дискретизации: {fs:.0f} Гц")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка фильтрации",
                                 f"Произошла ошибка при применении фильтра:\n{str(e)}")

    def parse_time_interval(self):
        return self.data_frame["dt"].iloc[0] if "dt" in self.data_frame.columns else 20e-6

    def add_spectrogram_button(self):
        spec_action = QAction(QIcon(get_resource_path("assets/iconSpectrogram.png")),
                              "Спектрограмма", self)
        spec_action.triggered.connect(self.show_spectrogram)
        self.toolbar.addAction(spec_action)

    def show_spectrogram(self):
        y = self.y_data.astype(float)

        dt = self.dt
        fs = 1.0 / dt

        experiment_time = self.parse_time_interval()

        print(f"[Info] Интервал дискретизации: {dt * 1e3:.3f} с")
        print(f"[Info] Частота дискретизации: {fs:.1f} Гц")
        print(f"[Info] Параметр эксперимента: {experiment_time:.1f} мс")
        print(f"[Info] Общее количество отсчетов: {len(y)}")

        total_duration = len(y) * dt
        print(f"[Info] Общая длительность сигнала: {total_duration * 1000:.1f} мс")

        window_duration = 0.002
        nperseg = int(window_duration * fs)

        if nperseg < 32:
            nperseg = 32
            window_duration = nperseg / fs
            print(f"[Warning] Окно увеличено до минимума: {window_duration * 1000:.1f} мс")

        max_window = len(y) // 4
        if nperseg > max_window:
            nperseg = max_window
            window_duration = nperseg / fs
            print(f"[Warning] Окно ограничено размером данных: {window_duration * 1000:.1f} мс")

        noverlap = int(nperseg * 0.80)
        actual_overlap_percent = (noverlap / nperseg) * 100

        print(f"[Info] Длина окна: {nperseg} отсчетов ({window_duration * 1000:.1f} мс)")
        print(f"[Info] Перекрытие: {noverlap} отсчетов ({actual_overlap_percent:.1f}%)")

        if nperseg <= 0 or nperseg > len(y):
            print("[Error] Некорректные параметры окна")
            return

        try:
            f, t, Z = stft(y, fs=fs,
                           nperseg=nperseg,
                           noverlap=noverlap,
                           window='hann',
                           padded=False,
                           boundary=None,
                           scaling='spectrum')
        except Exception as e:
            print(f"[Error] Ошибка при вычислении STFT: {e}")
            return

        S = np.abs(Z) ** 2

        S_dB = 10 * np.log10(S + 1e-12)

        S_dB = S_dB.T

        print(f"[Info] Частотное разрешение: {f[1] - f[0]:.2f} Гц")
        print(f"[Info] Временное разрешение: {(t[1] - t[0]) * 1000:.2f} мс")
        print(f"[Info] Максимальная частота: {f[-1]:.1f} Гц")
        print(f"[Info] Размер спектрограммы: {S_dB.shape} (время × частота)")

        Y_full = np.abs(np.fft.rfft(y))
        freqs_full = np.fft.rfftfreq(len(y), dt)
        peak_freq = freqs_full[np.argmax(Y_full)]
        print(f"[Info] Доминирующая частота: {peak_freq:.1f} Гц")

        if self.plot_widget is not None:
            self.layout.removeWidget(self.plot_widget)
            self.plot_widget.deleteLater()
            self.plot_widget = None

        glw = GraphicsLayoutWidget()
        glw.setBackground('w')

        p = glw.addPlot(row=0, col=0)
        p.showGrid(x=True, y=True, alpha=0.3)
        p.setLabel('bottom', 'Время', units='с')
        p.setLabel('left', 'Частота', units='Гц')
        p.setTitle('Спектрограмма ЭМГ-сигнала')

        img = ImageItem(S_dB)

        rect = QRectF(t[0], f[0], t[-1] - t[0], f[-1] - f[0])
        img.setRect(rect)
        p.addItem(img)

        colors = [
            (0.0, (0, 0, 139)),
            (0.1, (0, 0, 255)),
            (0.2, (0, 100, 255)),
            (0.3, (0, 255, 255)),
            (0.4, (0, 255, 100)),
            (0.5, (0, 255, 0)),
            (0.6, (100, 255, 0)),
            (0.7, (255, 255, 0)),
            (0.8, (255, 150, 0)),
            (0.9, (255, 50, 0)),
            (1.0, (139, 0, 0))
        ]

        cmap = pg.ColorMap(
            pos=[c[0] for c in colors],
            color=[c[1] for c in colors]
        )

        lut = cmap.getLookupTable(0.0, 1.0, 2048)
        img.setLookupTable(lut)
        img.setLevels([S_dB.min(), S_dB.max()])

        max_display_freq = min(500, f[-1], fs / 2)
        print(f"[Debug] max_display_freq = {max_display_freq} Гц")
        print(f"[Debug] f[-1] = {f[-1]} Гц")
        print(f"[Debug] fs/2 = {fs / 2} Гц")
        p.setYRange(0, max_display_freq)
        p.setXRange(t[0], t[-1])

        p.setAspectLocked(False)
        p.getViewBox().setMenuEnabled(True)
        p.getViewBox().setMouseEnabled(x=True, y=True)

        cbar = ColorBarItem(
            values=(S_dB.min(), S_dB.max()),
            colorMap=cmap,
            interactive=False,
            label='Спектральная плотность (дБ)',
            width=20
        )
        glw.addItem(cbar, row=0, col=1)

        self.plot_widget = glw
        self.layout.addWidget(self.plot_widget)

        print(f"[Info] Спектрограмма построена успешно")

        self.spectrogram_data = {
            'frequencies': f,
            'times': t,
            'spectrogram': S_dB,
            'original_data': y,
            'fs': fs,
            'dt': dt,
            'window_duration': window_duration * 1000,
            'overlap_percent': actual_overlap_percent
        }

    def create_plot(self):
        plot_widget = pg.PlotWidget()
        plot_widget.setBackground("w")
        plot_item = plot_widget.getPlotItem()
        plot_item.setMenuEnabled(False)
        plot_widget.showGrid(x=True, y=True, alpha=0.5)

        self.x_data = self.data_frame["Time (µs)"].values
        self.y_data = self.data_frame["Voltage (mV)"].values

        self.dt = self.data_frame["dt"].iloc[0] if "dt" in self.data_frame.columns else 20e-6

        fs = 1.0 / self.dt
        total_time_ms = (self.x_data[-1] - self.x_data[0]) / 1000

        print(f"[Graph] Частота дискретизации: {fs:.0f} Гц")
        print(f"[Graph] Общая длительность: {total_time_ms:.2f} мс")
        print(f"[Graph] Интервал дискретизации: {self.dt * 1e6:.2f} мкс")
        print(f"[Graph] Количество отсчетов: {len(self.y_data)}")

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
            x = np.fft.rfftfreq(len(self.x_data), d=self.dt)

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
        if self.plot_widget is not None:
            self.layout.removeWidget(self.plot_widget)
            self.plot_widget.deleteLater()
            self.plot_widget = None
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
                if isinstance(self.plot_widget, GraphicsLayoutWidget):
                    pixmap = self.plot_widget.grab()
                    pixmap.save(file_path)
                else:
                    exporter = pyqtgraph.exporters.ImageExporter(self.plot_widget.plotItem)
                    exporter.export(file_path)

                QMessageBox.information(self, "Экспорт завершен", f"График сохранен как {file_path}")

            elif file_type.startswith("CSV"):
                if isinstance(self.plot_widget, GraphicsLayoutWidget):
                    if hasattr(self, 'spectrogram_data'):
                        self.export_spectrogram_csv(file_path)
                        QMessageBox.information(self, "Экспорт завершен",
                                                f"Данные спектрограммы сохранены как {file_path}")
                    else:
                        QMessageBox.information(self, "Информация", "Данные спектрограммы недоступны для экспорта")
                else:
                    np.savetxt(file_path, np.column_stack((self.x_data, self.y_data)), delimiter=",",
                               header="Time(µs),Voltage (mV)", comments="")
                    QMessageBox.information(self, "Экспорт завершен", f"График сохранен как {file_path}")

            elif file_type.startswith("Excel"):
                if isinstance(self.plot_widget, GraphicsLayoutWidget):
                    if hasattr(self, 'spectrogram_data'):
                        self.export_spectrogram_excel(file_path)
                        QMessageBox.information(self, "Экспорт завершен",
                                                f"Данные спектрограммы сохранены как {file_path}")
                    else:
                        QMessageBox.information(self, "Информация", "Данные спектрограммы недоступны для экспорта")
                else:
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

        if isinstance(self.plot_widget, GraphicsLayoutWidget):
            pixmap = self.plot_widget.grab()
            painter.drawPixmap(0, 0, pixmap)
        else:
            self.plot_widget.render(painter)

        painter.end()
        QMessageBox.information(self, "Экспорт завершен", f"График сохранен как {file_path}")

    def save_as_excel(self, file_path):
        df = pd.DataFrame({"Time (µs)": self.x_data, "Voltage (mV)": self.y_data})
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
