import pytesseract
from pytesseract import Output
import os
import sys

def get_tesseract_path():

    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..")
        )

    return os.path.join(base_path, "tesseract", "tesseract.exe")


pytesseract.pytesseract.tesseract_cmd = get_tesseract_path()


def tesseract_ocr_lines(image):

    data = pytesseract.image_to_data(
        image,
        config="--oem 3 --psm 6",
        output_type=Output.DICT
    )

    lines = {}
    confidences = []

    n = len(data["text"])

    for i in range(n):
        word = data["text"][i].strip()
        conf = int(data["conf"][i])

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

    avg_conf = sum(confidences) / len(confidences) if confidences else 0.0

    return ordered_lines, avg_conf


def extract_text(image):

    lines, conf = tesseract_ocr_lines(image)

    return {
        "text": "\n".join(lines),
        "lines": lines,
        "confidence": round(conf, 2),
        "engine": "tesseract",
        "data": pytesseract.image_to_data(
            image,
            config="--oem 3 --psm 6",
            output_type=Output.DICT
        )
    }