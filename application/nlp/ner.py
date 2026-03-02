import re
import spacy

nlp = spacy.load("en_core_web_sm")

# ---------------------------
# REGEX PATTERNS
# ---------------------------

# Phone detection (international, OCR tolerant)
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
    # 1️⃣ PHONE (Robust International Logic)
    # ---------------------------
    phone_candidates = PHONE_PATTERN.findall(text)

    for candidate in phone_candidates:

        # Remove unwanted characters but keep +
        cleaned = re.sub(r'[^\d+]', '', candidate)

        # Fix multiple + signs (OCR noise)
        if cleaned.count('+') > 1:
            cleaned = cleaned.replace('+', '', cleaned.count('+') - 1)

        digits_only = re.sub(r'\D', '', cleaned)

        # Valid international phone numbers are usually 8–15 digits
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

        # Name usually first line
        if len(lines) >= 1:
            entities["Name"] = lines[0].title()

        # Designation usually second line
        if len(lines) >= 2:
            entities["Designation"] = lines[1].title()

        # Address detection
        address_lines = []
        address_started = False

        for line in lines:

            lower = line.lower()

            # Skip lines that contain phone/email/website
            if (
                entities["Phone"] and entities["Phone"] in line
                or entities["Email"] and entities["Email"] in line
                or entities["Website"] and entities["Website"] in line
            ):
                continue

            # Strong address indicators
            if PINCODE.search(line):
                address_started = True

            if any(word in lower for word in [
                "street", "st", "road", "rd",
                "nagar", "layout", "avenue",
                "floor", "building", "block",
                "near", "opposite"
            ]):
                address_started = True

            if address_started:
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