import json


class JsonFileHandler:
    def __init__(self, file_path):
        self.file_path = file_path
        self.data = self.load_data()

    def load_data(self):
        try:
            with open(self.file_path, "r", encoding="utf-8") as file:
                return json.load(file)
        except FileNotFoundError:
            return []
        except json.JSONDecodeError:
            return []

    def save_data(self):
        with open(self.file_path, "w", encoding="utf-8") as file:
            json.dump(self.data, file, indent=4, ensure_ascii=False)

    def get_filename(self, sample, time_ms, type_, type_2, subtype):
        for entry in self.data:
            if (entry["sample"] == sample and entry["time_ms"] == time_ms and
                    entry["type"] == type_ and entry["type_2"] == type_2 and entry["subtype"] == subtype):
                return entry["filename"].replace(".txt", "")
        return None

    def update_filename(self, sample, time_ms, type_, type_2, subtype, new_filename):
        for entry in self.data:
            if (entry["sample"] == sample and entry["time_ms"] == time_ms and
                    entry["type"] == type_ and entry["type_2"] == type_2 and entry["subtype"] == subtype):
                entry["filename"] = f"{new_filename}.txt"
                self.save_data()
                return True
        return False

    def find_by_filename(self, filename):
        for entry in self.data:
            if entry["filename"] == filename:
                return {
                    "sample": entry["sample"],
                    "time_ms": entry["time_ms"],
                    "type": entry["type"],
                    "type_2": entry["type_2"],
                    "subtype": entry["subtype"]
                }
        return None
