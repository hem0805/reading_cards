import re
import spacy

nlp = spacy.load("en_core_web_sm")

PHONE = re.compile(r'(\+?\d[\d\s\-()]{8,}\d)')
EMAIL = re.compile(r'[\w\.-]+@[\w\.-]+\.\w+')
WEBSITE = re.compile(
    r'\b((?:https?://)?(?:www\.)?[a-zA-Z0-9-]+\.(?:com|in|org|net|co|io|ai|edu|gov)(?:/[^\s]*)?)\b',
    re.IGNORECASE
)
LINKEDIN = re.compile(r'(linkedin\.com/\S+)', re.I)

DESIGNATIONS = [
    "engineer", "manager", "director", "sales",
    "marketing", "consultant", "founder", "ceo", "cto","developer","executive",
    "principal","architect","qa","software","zona","professor","peoject","head","associate",
    "owner","builder"
]


def extract_entities(text, lines=None):
    """
    Extract entities from OCR text.
    Uses:
    - line position (preferred)
    - regex (high confidence)
    - spaCy (fallback)
    """

    entities = {
        "Name": None,
        "Designation": None,
        "Phone": None,
        "Email": None,
        "Website": None,
        "LinkedIn": None
    }

    if not text or len(text.strip()) < 10:
        return entities

    # ---------------------------
    # 1️⃣ LINE-AWARE HEURISTICS
    # ---------------------------
    if lines:
        # Name is usually first line (all caps or title case)
        if not entities["Name"] and len(lines) >= 1:
            entities["Name"] = lines[0].title()

        # Designation often second line
        if not entities["Designation"] and len(lines) >= 2:
            entities["Designation"] = lines[1].title()

    # ---------------------------
    # 2️⃣ REGEX (MOST RELIABLE)
    # ---------------------------
    if m := PHONE.search(text):
        entities["Phone"] = m.group(1)

    if m := EMAIL.search(text):
        entities["Email"] = m.group(0)

    if m := WEBSITE.search(text):
        entities["Website"] = m.group(0)

    if m := LINKEDIN.search(text):
        entities["LinkedIn"] = m.group(1)

    # ---------------------------
    # 3️⃣ spaCy (FALLBACK)
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