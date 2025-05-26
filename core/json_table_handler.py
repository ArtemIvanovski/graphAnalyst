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

    def get_filename(self, sample, time_ms, pickling_time, localization, intensity):
        for entry in self.data:
            if (entry["sample"] == sample and entry["time_ms"] == time_ms and
                    entry["pickling_time"] == pickling_time and entry["localization"] == localization and entry["intensity"] == intensity):
                return entry["filename"].replace(".txt", "")
        return None

    def update_filename(self, sample, time_ms, pickling_time, localization, intensity, new_filename):
        for entry in self.data:
            if (entry["sample"] == sample and entry["time_ms"] == time_ms and
                    entry["pickling_time"] == pickling_time and entry["localization"] == localization and entry["intensity"] == intensity):
                entry["filename"] = f"{new_filename}.txt"
                self.save_data()
                return True
        return False

    def find_by_filename(self, filename):
        for entry in self.data:
            if entry["filename"] == filename:
                return {
                    "Образец": entry["sample"],
                    "Время": entry["time_ms"],
                    "Время протравливания": entry["pickling_time"],
                    "Локализация": entry["localization"],
                    "Интенсивность": entry["intensity"]
                }
        return None

    def search_entries(self, query="", filters=None):
        if filters is None:
            filters = {}

        results = []
        for entry in self.data:
            if query and not any(query.lower() in str(entry[key]).lower() for key in entry):
                continue

            match = True
            for key, value in filters.items():
                if value != "Не важно" and str(entry.get(key, "")) != value:
                    match = False
                    break

            if match:
                results.append(entry)

        return results

    def get_all_values_for_key(self, key):
        return sorted(set(str(entry.get(key, "")) for entry in self.data))