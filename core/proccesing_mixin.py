from GUI.error_window import ErrorWindow
from GUI.graph_window import GraphWindow
from GUI.loading_window import LoadingWindow
from core.threads.file_processing_thread import FileProcessingThread


class ProcessingMixin:
    def start_processing(self, file_path):
        self.loading_window = LoadingWindow(self)
        self.loading_window.show()

        self.file_processing_thread = FileProcessingThread(file_path, self.json_file_handler)
        self.file_processing_thread.finished.connect(self.on_processing_finished)
        self.file_processing_thread.start()

    def on_processing_finished(self, metadata, status):
        self.loading_window.close()

        if status == "error":
            error_dialog = ErrorWindow(f"Ошибка обработки файла: {metadata.get('error', 'Неизвестная ошибка')}")
            error_dialog.exec_()
            return

        data_frame = self.file_processing_thread.data_frame
        self.open_graph_window(metadata, data_frame)

    def open_graph_window(self, metadata, data_frame):
        self.graph_window = GraphWindow(metadata, data_frame, self.filename)
        self.graph_window.show()
