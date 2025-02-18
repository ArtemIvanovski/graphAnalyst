from PyQt5.QtCore import QThread, pyqtSignal

from core.parser import parse_file_with_metadata


class FileProcessingThread(QThread):
    finished = pyqtSignal(dict, str)

    def __init__(self, file_path):
        super().__init__()
        self.file_path = file_path
        self.data_frame = None

    def run(self):
        try:
            metadata, data = parse_file_with_metadata(self.file_path)
            self.data_frame = data
            self.finished.emit(metadata, "success")
        except Exception as e:
            self.finished.emit({"error": str(e)}, "error")
