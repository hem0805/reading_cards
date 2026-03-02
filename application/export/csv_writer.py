import csv
import os
import pandas as pd
from datetime import datetime

CSV_PATH = "outputs/extracted.csv"

# Strict schema (order matters)
FIELDS = [
    "Name",
    "Designation",
    "Phone",
    "Email",
    "Website",
    "Address",
    "Timestamp"
]


# -------------------------------------------------
# Save Record to CSV
# -------------------------------------------------
def append_to_csv(data):
    os.makedirs("outputs", exist_ok=True)

    data_copy = data.copy()
    data_copy["Timestamp"] = datetime.now().isoformat(timespec="seconds")

    # Enforce column order and prevent extra keys
    row = {field: data_copy.get(field, "") or "" for field in FIELDS}

    file_exists = os.path.isfile(CSV_PATH)

    with open(CSV_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)

        # Write header only once
        if not file_exists:
            writer.writeheader()

        writer.writerow(row)


# -------------------------------------------------
# Duplicate Detection
# Email = Primary Key
# Phone = Fallback (only if email missing)
# -------------------------------------------------
def is_duplicate(record):

    if not os.path.exists(CSV_PATH):
        return False

    try:
        df = pd.read_csv(CSV_PATH)
    except Exception:
        return False

    if df.empty:
        return False

    email = str(record.get("Email", "")).strip().lower()
    phone = str(record.get("Phone", "")).strip()

    # 1️⃣ Email is Primary Key
    if email and "Email" in df.columns:
        existing_emails = df["Email"].astype(str).str.strip().str.lower()
        if email in existing_emails.values:
            return "email"

    # 2️⃣ Phone fallback only if email missing
    if not email and phone and "Phone" in df.columns:
        existing_phones = df["Phone"].astype(str).str.strip()
        if phone in existing_phones.values:
            return "phone"

    return False


# -------------------------------------------------
# Get CSV Path (for download)
# -------------------------------------------------
def get_csv_path():
    return CSV_PATH