import pytesseract
from pytesseract import Output
import os
import sys
import cv2


# =========================================
# TESSERACT PATH (EXE SAFE)
# =========================================

def get_tesseract_path():

    if getattr(sys, "frozen", False):
        # Running as EXE
        base_path = sys._MEIPASS
    else:
        # Running in normal Python
        base_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..")
        )

    tesseract_path = os.path.join(base_path, "tesseract", "tesseract.exe")

    if not os.path.exists(tesseract_path):
        raise FileNotFoundError(f"Tesseract not found at: {tesseract_path}")

    return tesseract_path


pytesseract.pytesseract.tesseract_cmd = get_tesseract_path()


# =========================================
# OCR LOGIC
# =========================================

def tesseract_ocr_lines(image):

    if image is None:
        raise ValueError("Invalid image passed to OCR")

    data = pytesseract.image_to_data(
        image,
        config="--oem 3 --psm 6",
        output_type=Output.DICT
    )

    lines = {}
    confidences = []

    n = len(data["text"])

    for i in range(n):

        word = str(data["text"][i]).strip()

        try:
            conf = int(float(data["conf"][i]))
        except:
            continue

        if not word or conf < 40:
            continue

        key = (
            data["block_num"][i],
            data["par_num"][i],
            data["line_num"][i]
        )

        lines.setdefault(key, []).append(word)
        confidences.append(conf)

    ordered_lines = [
        " ".join(words)
        for _, words in sorted(lines.items())
    ]

    avg_conf = (
        sum(confidences) / len(confidences)
        if confidences else 0.0
    )

    return ordered_lines, avg_conf, data


# =========================================
# PUBLIC FUNCTION
# =========================================

def extract_text(image):

    lines, conf, raw_data = tesseract_ocr_lines(image)

    return {
        "text": "\n".join(lines),
        "lines": lines,
        "confidence": round(conf, 2),
        "engine": "tesseract",
        "data": raw_data
    }