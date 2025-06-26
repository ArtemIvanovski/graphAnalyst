import json
import os


def generate_json_entries():
    """
    Генерирует JSON записи для библиотеки файлов
    """

    # Определяем структуру данных
    pickling_times = ["без протравливания", "15 с", "30 с", "45 с", "60 с"]
    localizations = ["вестибулярная поверхность", "пришеечная область"]
    intensities = ["слабая", "сильная"]

    print("=== Генератор JSON для библиотеки файлов ===\n")

    # Запрашиваем основные параметры
    try:
        sample = int(input("Введите номер образца (sample): "))
        time_ms = int(input("Введите время в миллисекундах (time_ms): "))
    except ValueError:
        print("Ошибка: Введите корректные числовые значения!")
        return None

    print(f"\nВы ввели: sample={sample}, time_ms={time_ms}")

    # Запрашиваем список файлов
    print("\nВведите имена файлов через пробел (20 файлов):")
    print("Порядок: без_протравливания(4) -> 15с(4) -> 30с(4) -> 45с(4) -> 60с(4)")
    print("Для каждого времени: вест_слабая, вест_сильная, приш_слабая, приш_сильная")
    print("Пример: 301 302 303 304 361 362 363 364 421 422 423 424 481 482 483 484 541 542 543 544")

    filenames_input = input("\nИмена файлов: ").strip()
    filenames = filenames_input.split()

    if len(filenames) != 20:
        print(f"Ошибка: Ожидается 20 файлов, получено {len(filenames)}")
        return None

    # Генерируем JSON записи
    entries = []
    file_index = 0

    for pickling_time in pickling_times:
        for localization in localizations:
            for intensity in intensities:
                if file_index < len(filenames):
                    filename = filenames[file_index]
                    if not filename.endswith('.txt'):
                        filename += '.txt'

                    entry = {
                        "sample": sample,
                        "time_ms": time_ms,
                        "pickling_time": pickling_time,
                        "localization": localization,
                        "intensity": intensity,
                        "filename": filename
                    }
                    entries.append(entry)
                    file_index += 1

    return entries


def display_generated_json(entries):
    """
    Отображает сгенерированный JSON
    """
    print("\n=== Сгенерированный JSON ===")
    print(json.dumps(entries, ensure_ascii=False, indent=4))


def save_to_file(entries):
    """
    Сохраняет JSON в файл table.json в папке D:\graph\library
    """
    save_choice = input("\nСохранить в table.json? (y/n): ").lower().strip()

    if save_choice == 'y' or save_choice == 'yes':
        # Фиксированный путь к файлу
        file_path = r"D:\graph\library\table.json"

        try:
            # Создаем папку если она не существует
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            # Если файл существует, загружаем существующие данные
            existing_data = []
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        existing_data = json.load(f)
                    print(f"Найден существующий файл table.json с {len(existing_data)} записями")
                except json.JSONDecodeError:
                    print(f"Файл table.json поврежден, создается новый")
                    existing_data = []
            else:
                print("Создается новый файл table.json")

            # Добавляем новые записи в конец
            existing_data.extend(entries)

            # Сохраняем объединенные данные
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, ensure_ascii=False, indent=4)

            print(f"Данные успешно добавлены в {file_path}")
            print(f"Общее количество записей в файле: {len(existing_data)}")
            print(f"Добавлено новых записей: {len(entries)}")

        except PermissionError:
            print("Ошибка: Недостаточно прав для записи в указанную папку")
        except FileNotFoundError:
            print("Ошибка: Указанный путь не найден")
        except Exception as e:
            print(f"Ошибка при сохранении: {e}")


def copy_to_clipboard(entries):
    """
    Копирует JSON в буфер обмена (опционально)
    """
    copy_choice = input("Скопировать JSON в буфер обмена? (y/n): ").lower().strip()

    if copy_choice == 'y' or copy_choice == 'yes':
        try:
            import pyperclip
            json_string = json.dumps(entries, ensure_ascii=False, indent=4)
            pyperclip.copy(json_string)
            print("JSON скопирован в буфер обмена!")
        except ImportError:
            print("Модуль pyperclip не установлен. Установите его командой: pip install pyperclip")
        except Exception as e:
            print(f"Ошибка при копировании: {e}")


def show_structure_help():
    """
    Показывает справку по структуре данных
    """
    print("\n=== Справка по структуре данных ===")
    print("Порядок файлов (всего 20):")

    pickling_times = ["без протравливания", "15 с", "30 с", "45 с", "60 с"]
    localizations = ["вестибулярная поверхность", "пришеечная область"]
    intensities = ["слабая", "сильная"]

    index = 1
    for i, pickling_time in enumerate(pickling_times):
        print(f"\n{pickling_time}:")
        for j, localization in enumerate(localizations):
            for k, intensity in enumerate(intensities):
                print(f"  {index:2d}. {localization} - {intensity}")
                index += 1


def main():
    """
    Основная функция программы
    """
    while True:
        print("\n" + "=" * 50)
        print("1. Сгенерировать JSON записи")
        print("2. Показать справку по структуре")
        print("3. Выход")
        print("=" * 50)

        choice = input("Выберите действие (1-3): ").strip()

        if choice == '1':
            entries = generate_json_entries()
            if entries:
                display_generated_json(entries)
                save_to_file(entries)
                copy_to_clipboard(entries)

        elif choice == '2':
            show_structure_help()

        elif choice == '3':
            print("До свидания!")
            break

        else:
            print("Неверный выбор. Попробуйте снова.")


if __name__ == "__main__":
    main()