import os
from datetime import datetime

VCARD_DIR = "outputs/vcards"
MASTER_VCARD = "outputs/contacts.vcf"


def generate_vcard_content(record):
    return f"""BEGIN:VCARD
VERSION:3.0
FN:{record.get('Name','')}
TITLE:{record.get('Designation','')}
TEL;TYPE=CELL:{record.get('Phone','')}
EMAIL:{record.get('Email','')}
URL:{record.get('Website','')}
ADR;TYPE=WORK:;;{record.get('Address','')}
NOTE:Scanned on {datetime.now().isoformat(timespec="seconds")}
END:VCARD
"""


def save_vcard(record):
    os.makedirs(VCARD_DIR, exist_ok=True)
    os.makedirs("outputs", exist_ok=True)

    vcard_content = generate_vcard_content(record)

    # Save individual file
    safe_name = record.get("Name", "contact").replace(" ", "_")
    file_path = os.path.join(VCARD_DIR, f"{safe_name}.vcf")

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(vcard_content)

    # Append to master file
    with open(MASTER_VCARD, "a", encoding="utf-8") as f:
        f.write(vcard_content + "\n")

    return file_path