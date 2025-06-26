import os
import shutil
import numpy as np
import pyqtgraph as pg
from pyqtgraph import GraphicsLayoutWidget, ImageItem, ColorBarItem
from PyQt5.QtCore import QRectF
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QPixmap, QPainter, QFont, QFontMetrics
from PyQt5.QtCore import Qt
from scipy.signal import stft
from core.parser import parse_file_with_metadata
from core.settings_handler import get_resource_path


class PosterProcessor:
    def __init__(self, json_file_handler):
        self.json_file_handler = json_file_handler
        self.temp_folder = get_resource_path("temp")

        # Очищаем папку temp перед началом
        if os.path.exists(self.temp_folder):
            shutil.rmtree(self.temp_folder)
        os.makedirs(self.temp_folder, exist_ok=True)

        # Настраиваем pyqtgraph для работы с белым фоном
        pg.setConfigOption('background', 'w')
        pg.setConfigOption('foreground', 'k')

    def create_poster(self, selected_params):
        pickling_times = ["без протравливания", "15 с", "30 с", "45 с", "60 с"]
        created_files = []

        print("[Info] Создание индивидуальных спектрограмм...")

        # Создаем отдельные спектрограммы
        for pickling_time in pickling_times:
            filters = selected_params.copy()
            filters["pickling_time"] = pickling_time

            results = self.json_file_handler.search_entries("", filters)

            if results:
                filename = results[0]["filename"]
                filepath = os.path.join("library", filename)
                full_path = get_resource_path(filepath)

                if os.path.exists(full_path):
                    output_file = self.process_single_file(full_path, pickling_time, selected_params)
                    if output_file:
                        created_files.append(output_file)
                        print(f"Создан файл: {output_file}")

        if len(created_files) == 5:
            print("[Info] Объединение спектрограмм в финальный плакат...")
            final_poster = self.combine_spectrograms(created_files, selected_params)
            if final_poster:
                return final_poster

        return None

    def process_single_file(self, file_path, pickling_time, params):
        try:
            # Парсим файл
            metadata, data_frame = parse_file_with_metadata(file_path, self.json_file_handler)

            x_data = data_frame["Index"].values
            y_data = data_frame["Voltage (mV)"].values.astype(float)

            # Создаем имя файла
            filename_base = f"{params['sample']}_{params['time_ms']}_{pickling_time.replace(' ', '_').replace('/', '_')}"
            output_path = os.path.join(self.temp_folder, f"{filename_base}.png")

            # Парсим интервал дискретизации
            time_interval_str = metadata.get("Time interval", "20.00000uS")

            if "uS" in str(time_interval_str) or "µS" in str(time_interval_str):
                dt = float(str(time_interval_str).replace("uS", "").replace("µS", "").strip()) * 1e-6
            elif "ms" in str(time_interval_str):
                dt = float(str(time_interval_str).replace("ms", "").strip()) * 1e-3
            else:
                dt = 20e-6

            dt = dt / 2
            fs = 1.0 / dt

            print(f"[Info] Обработка файла: {os.path.basename(file_path)}")
            print(f"[Info] Время протравливания: {pickling_time}")

            # Настройки для STFT
            window_duration = 0.002
            nperseg = int(window_duration * fs)

            if nperseg < 32:
                nperseg = 32
                window_duration = nperseg / fs

            max_window = len(y_data) // 4
            if nperseg > max_window:
                nperseg = max_window
                window_duration = nperseg / fs

            noverlap = int(nperseg * 0.80)

            if nperseg <= 0 or nperseg > len(y_data):
                print(f"[Error] Некорректные параметры окна для файла {file_path}")
                return None

            # Вычисляем STFT
            f, t, Z = stft(y_data, fs=fs,
                           nperseg=nperseg,
                           noverlap=noverlap,
                           window='hann',
                           padded=False,
                           boundary=None,
                           scaling='spectrum')

            S = np.abs(Z) ** 2
            S_dB = 10 * np.log10(S + 1e-12)
            S_dB = S_dB.T

            # Создаем GraphicsLayoutWidget для отдельной спектрограммы
            glw = GraphicsLayoutWidget()
            glw.resize(520, 420)  # Размер для горизонтальной компоновки
            glw.setBackground('w')

            # Добавляем заголовок с временем протравливания
            title_text = f"{pickling_time}"
            title_label = glw.addLabel(title_text, row=0, col=0, colspan=2)
            title_label.setText(title_text, size='12pt', bold=True)

            # Спектрограмма
            p2 = glw.addPlot(row=1, col=0)
            p2.showGrid(x=True, y=True, alpha=0.3)
            p2.setLabel('bottom', 'Время (с)', size='12pt')
            p2.setLabel('left', 'Частота (Гц)', size='12pt')

            # Создаем изображение спектрограммы
            img = ImageItem(S_dB)
            rect = QRectF(t[0], f[0], t[-1] - t[0], f[-1] - f[0])
            img.setRect(rect)
            p2.addItem(img)

            # Настраиваем цветовую карту
            colors = [
                (0.0, (0, 0, 139)),  # темно-синий
                (0.1, (0, 0, 255)),  # синий
                (0.2, (0, 100, 255)),  # голубой
                (0.3, (0, 255, 255)),  # циан
                (0.4, (0, 255, 100)),  # светло-зеленый
                (0.5, (0, 255, 0)),  # зеленый
                (0.6, (100, 255, 0)),  # желто-зеленый
                (0.7, (255, 255, 0)),  # желтый
                (0.8, (255, 150, 0)),  # оранжевый
                (0.9, (255, 50, 0)),  # красно-оранжевый
                (1.0, (139, 0, 0))  # темно-красный
            ]

            cmap = pg.ColorMap(
                pos=[c[0] for c in colors],
                color=[c[1] for c in colors]
            )

            lut = cmap.getLookupTable(0.0, 1.0, 2048)
            img.setLookupTable(lut)
            img.setLevels([S_dB.min(), S_dB.max()])

            # View All
            p2.setXRange(t[0], t[-1])
            p2.setYRange(f[0], f[-1])
            p2.setAspectLocked(False)
            p2.getViewBox().setMenuEnabled(False)
            p2.getViewBox().setMouseEnabled(x=False, y=False)

            # Добавляем маленькую цветовую шкалу
            cbar = ColorBarItem(
                values=(S_dB.min(), S_dB.max()),
                colorMap=cmap,
                interactive=False,
                width=20
            )
            glw.addItem(cbar, row=1, col=1)

            # Обновляем интерфейс
            QApplication.processEvents()

            # Сохраняем
            pixmap = glw.grab()
            success = pixmap.save(output_path, "PNG")

            if success:
                print(f"[Success] Сохранено: {output_path}")
                return output_path
            else:
                print(f"[Error] Не удалось сохранить файл: {output_path}")
                return None

        except Exception as e:
            print(f"[Error] Ошибка при обработке файла {file_path}: {e}")
            import traceback
            traceback.print_exc()
            return None

    def combine_spectrograms(self, created_files, params):
        try:
            # Размеры финального плаката (1920x1080)
            final_width = 1920
            final_height = 1080

            # Создаем финальный QPixmap
            final_pixmap = QPixmap(final_width, final_height)
            final_pixmap.fill(Qt.white)

            painter = QPainter(final_pixmap)

            # Размеры для каждой спектрограммы
            margin = 25  # Отступ между спектрограммами
            spec_width = 600  # Ширина спектрограммы
            spec_height = 500  # Высота спектрограммы

            # Начальные координаты
            start_x = 40
            start_y = 50

            # Позиции для размещения спектрограмм
            # Первая строка: без протравливания, 15 с, 30 с
            # Вторая строка: 45 с, 60 с
            positions = {
                "без_протравливания": (start_x, start_y),  # первая строка, первая колонка
                "15_с": (start_x + spec_width + margin, start_y),  # первая строка, вторая колонка
                "30_с": (start_x + 2 * (spec_width + margin), start_y),  # первая строка, третья колонка
                "45_с": (start_x, start_y + spec_height + margin),  # вторая строка, первая колонка
                "60_с": (start_x + spec_width + margin, start_y + spec_height + margin),
                # вторая строка, вторая колонка
            }

            # Размещаем спектрограммы
            for file_path in created_files:
                filename = os.path.basename(file_path)

                # Определяем время протравливания из имени файла
                if "без_протравливания" in filename:
                    pos = positions["без_протравливания"]
                elif "15_с" in filename:
                    pos = positions["15_с"]
                elif "30_с" in filename:
                    pos = positions["30_с"]
                elif "45_с" in filename:
                    pos = positions["45_с"]
                elif "60_с" in filename:
                    pos = positions["60_с"]
                else:
                    continue

                # Загружаем и размещаем изображение
                spec_pixmap = QPixmap(file_path)
                if not spec_pixmap.isNull():
                    # Масштабируем до нужного размера
                    spec_pixmap = spec_pixmap.scaled(spec_width, spec_height, Qt.KeepAspectRatio,
                                                     Qt.SmoothTransformation)
                    painter.drawPixmap(pos[0], pos[1], spec_pixmap)

            # Добавляем характеристики справа от второй строки спектрограмм
            characteristics_x = start_x + 2 * (spec_width + margin)
            characteristics_y = start_y + spec_height + margin + 50  # Рядом со второй строкой
            characteristics_width = final_width - characteristics_x - 50
            characteristics_height = 300

            self.add_characteristics_text(painter, params,
                                          (characteristics_x, characteristics_y),
                                          (characteristics_width, characteristics_height))

            painter.end()

            # Сохраняем финальный плакат
            final_path = os.path.join(self.temp_folder, "final_poster.png")
            success = final_pixmap.save(final_path, "PNG")

            if success:
                print(f"[Success] Финальный плакат сохранен: {final_path}")
                return final_path
            else:
                print("[Error] Не удалось сохранить финальный плакат")
                return None

        except Exception as e:
            print(f"[Error] Ошибка при объединении спектрограмм: {e}")
            import traceback
            traceback.print_exc()
            return None

    def add_characteristics_text(self, painter, params, position, size):
        """Добавляет характеристики в указанную область"""
        try:
            # Настройка шрифта (размер 20)
            font = QFont("Arial", 16, QFont.Bold)
            painter.setFont(font)

            # Цвет рамки и текста
            painter.setPen(Qt.black)

            # Текст характеристик
            characteristics = [
                "Характеристики образца:",
                "",
                f"Образец: {params['sample']}",
                f"Время: {params['time_ms']} мс",
                f"Локализация: {params['localization']}",
                f"Интенсивность: {params['intensity']}"
            ]

            # Рисуем текст
            y_offset = position[1] + 40
            line_height = 35

            for line in characteristics:
                painter.drawText(position[0] + 25, y_offset, line)
                y_offset += line_height

        except Exception as e:
            print(f"[Error] Ошибка при добавлении характеристик: {e}")

    def cleanup_temp_folder(self):
        """Очищает временную папку"""
        try:
            if os.path.exists(self.temp_folder):
                shutil.rmtree(self.temp_folder)
                print("[Info] Временная папка очищена")
        except Exception as e:
            print(f"[Warning] Не удалось очистить временную папку: {e}")