import re
import spacy
import os
import sys
import en_core_web_sm

# def resource_path(relative_path):
#     try:
#         base_path = sys._MEIPASS
#     except Exception:
#         base_path = os.path.abspath(".")

#     return os.path.join(base_path, relative_path)

# model_path = resource_path("en_core_web_sm-3.8.0")

# nlp = spacy.load(model_path)

nlp=en_core_web_sm.load()

PHONE_PATTERN = re.compile(r'\+?\d[\d\s\-\(\)\.]{6,}\d')

EMAIL = re.compile(r'[\w\.-]+@[\w\.-]+\.\w+')

WEBSITE = re.compile(
    r'\b((?:https?://)?(?:www\.)?[a-zA-Z0-9-]+\.(?:com|in|org|net|co|io|ai|edu|gov)(?:/[^\s]*)?)\b',
    re.IGNORECASE
)

PINCODE = re.compile(r'\b\d{5,6}\b')


# ---------------------------
# ENTITY EXTRACTION
# ---------------------------

def extract_entities(text, lines=None):

    entities = {
        "Name": None,
        "Designation": None,
        "Phone": None,
        "Email": None,
        "Website": None,
        "Address": None
    }

    if not text or len(text.strip()) < 10:
        return entities

    # ---------------------------
    # 1️⃣ PHONE
    # ---------------------------
    phone_candidates = PHONE_PATTERN.findall(text)

    for candidate in phone_candidates:
        cleaned = re.sub(r'[^\d+]', '', candidate)

        if cleaned.count('+') > 1:
            cleaned = cleaned.replace('+', '', cleaned.count('+') - 1)

        digits_only = re.sub(r'\D', '', cleaned)

        if 8 <= len(digits_only) <= 15:
            if cleaned.startswith('+'):
                entities["Phone"] = '+' + digits_only
            else:
                entities["Phone"] = digits_only
            break

    # ---------------------------
    # 2️⃣ EMAIL
    # ---------------------------
    if m := EMAIL.search(text):
        entities["Email"] = m.group(0)

    # ---------------------------
    # 3️⃣ WEBSITE
    # ---------------------------
    if m := WEBSITE.search(text):
        entities["Website"] = m.group(0)

    # ---------------------------
    # 4️⃣ LINE-BASED HEURISTICS
    # ---------------------------
    if lines:

        # Remove empty lines
        lines = [l.strip() for l in lines if l.strip()]

        # ---- NAME (First clean line without digits) ----
        for line in lines:
            if not any(char.isdigit() for char in line) and len(line.split()) <= 4:
                entities["Name"] = line.title()
                break

        # ---- DESIGNATION (Keyword-based) ----
        designation_keywords = [
            "director", "manager", "architect", "engineer",
            "consultant", "principal", "officer", "head",
            "lead", "analyst", "developer", "executive"
        ]

        for line in lines:
            lower = line.lower()
            if any(word in lower for word in designation_keywords):
                entities["Designation"] = line.title()
                break

        # ---- ADDRESS DETECTION (Improved Logic) ----
        address_lines = []

        address_keywords = [
            "street", "st", "road", "rd",
            "nagar", "layout", "avenue",
            "floor", "building", "block",
            "near", "opposite", "india",
            "tamilnadu", "coimbatore",
            "pvt", "ltd"
        ]

        for line in lines:

            lower = line.lower()

            # Skip phone/email/website lines
            if (
                entities["Phone"] and entities["Phone"] in line
                or entities["Email"] and entities["Email"] in line
                or entities["Website"] and entities["Website"] in line
            ):
                continue

            if (
                PINCODE.search(line)
                or any(word in lower for word in address_keywords)
                or re.search(r'\d{2,}[-/]\d+', line)  # building number like 47-1
            ):
                address_lines.append(line)

        if address_lines:
            entities["Address"] = ", ".join(address_lines)

    # ---------------------------
    # 5️⃣ spaCy fallback for PERSON
    # ---------------------------
    try:
        doc = nlp(text)
        for ent in doc.ents:
            if ent.label_ == "PERSON" and not entities["Name"]:
                entities["Name"] = ent.text
                break
    except Exception:
        pass

    return entities