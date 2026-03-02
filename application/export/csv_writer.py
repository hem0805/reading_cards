import csv
import os
from datetime import datetime

CSV_PATH = "outputs/extracted.csv"

FIELDS = [
    "Name",
    "Designation",
    "Phone",
    "Email",
    "Website",
    "Address",
    "Timestamp"
]


def append_to_csv(data):
    os.makedirs("outputs", exist_ok=True)

    data_with_time = data.copy()
    data_with_time["Timestamp"] = datetime.now().isoformat(timespec="seconds")

    row = {field: data_with_time.get(field, "") or "" for field in FIELDS}

    write_header = False

    if not os.path.exists(CSV_PATH):
        write_header = True
    else:
        # Check if file has correct header
        with open(CSV_PATH, "r", encoding="utf-8") as f:
            first_line = f.readline().strip()
            if first_line != ",".join(FIELDS):
                write_header = True

    # If header missing or wrong, rewrite file properly
    if write_header:
        with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerow(row)
    else:
        with open(CSV_PATH, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDS)
            writer.writerow(row)


def get_csv_path():
    return CSV_PATH