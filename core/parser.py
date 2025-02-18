import pandas as pd


def parse_file_with_metadata(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()

    metadata = parse_metadata(lines)
    df = parse_data(lines)

    return metadata, df


def parse_metadata(lines):
    metadata = {}
    for line in lines:
        if ':' in line:
            key, value = map(str.strip, line.split(":", 1))
            metadata[key] = value
        elif line.strip().startswith("index"):
            break
    return metadata


def parse_data(lines):
    data = []
    start_idx = next(i for i, line in enumerate(lines) if line.strip().startswith("index"))

    for line in lines[start_idx + 1:]:
        line = line.strip()
        if line:
            parts = line.split()
            if len(parts) >= 2:
                index, voltage = int(parts[0]), float(parts[1])
                data.append((index, voltage))

    df = pd.DataFrame(data, columns=["Index", "Voltage (mV)"])
    return df
