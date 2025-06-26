from PyQt5.QtCore import QThread, pyqtSignal
from core.poster_processor import PosterProcessor


class PosterProcessingThread(QThread):
    finished = pyqtSignal(str, str, str)  # final_poster_path, temp_folder, status

    def __init__(self, selected_params, json_file_handler):
        super().__init__()
        self.selected_params = selected_params
        self.json_file_handler = json_file_handler
        self.final_poster_path = None
        self.temp_folder = None

    def run(self):
        try:
            processor = PosterProcessor(self.json_file_handler)
            self.temp_folder = processor.temp_folder
            self.final_poster_path = processor.create_poster(self.selected_params)

            if self.final_poster_path:
                self.finished.emit(self.final_poster_path, self.temp_folder, "success")
            else:
                self.finished.emit("", "", "error: Не удалось создать плакат")

        except Exception as e:
            self.finished.emit("", "", f"error: {str(e)}")