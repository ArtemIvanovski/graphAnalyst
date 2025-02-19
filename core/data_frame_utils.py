def validate_file_format(file_path):
    try:
        with open(file_path, 'r') as file:
            content = file.read()
            required_keywords = ["Channel", "Frequency", "index"]
            return all(keyword in content for keyword in required_keywords)
    except Exception:
        return False
