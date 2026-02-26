import csv
import os
from datetime import datetime

CSV_PATH = "outputs/extracted.csv"

FIELDS = [
    "Name", "Designation", "Phone", "Email",
    "Website", "LinkedIn", "OCR_Confidence", "Timestamp"
]


def append_to_csv(data):
    os.makedirs("outputs", exist_ok=True)
    data["Timestamp"] = datetime.now().isoformat(timespec="seconds")

    row = {k: data.get(k, "") or "" for k in FIELDS}
    exists = os.path.isfile(CSV_PATH)

    with open(CSV_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        if not exists:
            writer.writeheader()
        writer.writerow(row)