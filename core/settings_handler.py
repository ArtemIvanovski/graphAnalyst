import os
import sys

from logger import logger
import json


def get_resource_path(relative_path):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


def read_settings_from_json(field):
    try:
        with open(get_resource_path("settings.json"), 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get(field)
    except FileNotFoundError as e:
        logger.error(f"File 'settings.json' not found: {e}")
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error in file 'settings.json': {e}")
    except Exception as e:
        logger.error(f"Error reading file 'settings.json': {e}")


def write_settings_to_json(settings):
    try:
        with open(get_resource_path("settings.json"), 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=4)
        logger.info(f"Settings successfully written to 'settings.json'.")
    except Exception as e:
        logger.error(f"Error writing to file 'settings.json': {e}")
