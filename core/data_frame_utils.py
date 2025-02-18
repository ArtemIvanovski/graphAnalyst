from core.settings_handler import read_settings_from_json


def validate_file_format(file_path):
    try:
        with open(file_path, 'r') as file:
            content = file.read()
            required_keywords = ["Channel", "Frequency", "index"]
            return all(keyword in content for keyword in required_keywords)
    except Exception:
        return False


def round_data(df):
    decimal_places = read_settings_from_json("decimal_places")
    column_name = "Voltage (mV)"
    df[column_name] = df[column_name].round(decimal_places)
    return df


def multiply_data(df, time_interval):
    try:
        multiplier = float(time_interval.replace("uS", "").strip())
    except ValueError:
        raise ValueError(f"Неверный формат Time interval: {time_interval}")

    df = df.copy()
    df["Index"] *= int(multiplier)
    return df

