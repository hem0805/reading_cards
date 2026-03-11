import os
import csv

CSV_PATH = "outputs/extracted.csv"

HEADERS = [
    "Name",
    "Designation",
    "Phone",
    "Email",
    "Website",
    "Address"
]


# ============================
# ENSURE CSV EXISTS
# ============================

def ensure_csv():

    os.makedirs("outputs", exist_ok=True)

    if not os.path.exists(CSV_PATH):
        with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=HEADERS)
            writer.writeheader()


# ============================
# DUPLICATE CHECK
# ============================

def is_duplicate(record):

    ensure_csv()

    email = (record.get("Email") or "").strip().lower()
    phone = (record.get("Phone") or "").strip()

    with open(CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:

            existing_email = (row.get("Email") or "").strip().lower()
            existing_phone = (row.get("Phone") or "").strip()

            # PRIMARY KEY → EMAIL
            if email and existing_email == email:
                return "email"

            # SECONDARY → PHONE (ONLY IF EMAIL NOT PROVIDED)
            if not email and phone and existing_phone == phone:
                return "phone"

    return None


# ============================
# APPEND TO CSV
# ============================

def append_to_csv(record):

    ensure_csv()

    with open(CSV_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=HEADERS)
        writer.writerow(record)