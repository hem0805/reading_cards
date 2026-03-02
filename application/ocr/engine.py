import pytesseract
from pytesseract import Output

pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)


def tesseract_ocr_lines(image):
    """
    Perform OCR and return:
    - list of text lines
    - average confidence
    - full OCR data (for bounding boxes)
    """
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

    avg_conf = sum(confidences) / len(confidences) if confidences else 0.0

    return ordered_lines, avg_conf, data


def extract_text(image):
    """
    Returns:
    - text
    - lines
    - confidence
    - engine
    - raw OCR data (for bounding boxes)
    """
    lines, conf, data = tesseract_ocr_lines(image)

    return {
        "text": "\n".join(lines),
        "lines": lines,
        "confidence": round(conf, 2),
        "engine": "tesseract",
        "data": data
    }