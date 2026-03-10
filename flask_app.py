from flask import Flask, render_template, request, jsonify, send_file
import os
import csv
import cv2
import pytesseract
from datetime import datetime

from application.ocr.engine import extract_text
from application.nlp.ner import extract_entities
from application.cv.annotate import draw_boxes

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "static/outputs"
EXPORT_FOLDER = "exports"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
os.makedirs(EXPORT_FOLDER, exist_ok=True)

# memory storage
saved_records = []


# ===============================
# HOME PAGE
# ===============================

@app.route("/")
def index():
    return render_template("index.html")


# ===============================
# IMAGE EXTRACTION
# ===============================

@app.route("/extract", methods=["POST"])
def extract():

    if "file" not in request.files:
        return jsonify({"error": "No file received"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400

    name, ext = os.path.splitext(file.filename)

    if ext == "":
        ext = ".jpg"

    filename = datetime.now().strftime("%Y%m%d%H%M%S") + "_" + name + ext
    filepath = os.path.join(UPLOAD_FOLDER, filename)

    file.save(filepath)

    # read image
    image = cv2.imread(filepath)

    # OCR
    ocr_result = extract_text(image)

    text = ocr_result["text"]
    lines = ocr_result["lines"]

    # NLP extraction
    fields = extract_entities(text, lines)

    # draw bounding boxes
    annotated = draw_boxes(image, ocr_result["data"])

    annotated_filename = "annotated_" + filename
    annotated_path = os.path.join(OUTPUT_FOLDER, annotated_filename)

    cv2.imwrite(annotated_path, annotated)

    return jsonify({
        "annotated_image": "/static/outputs/" + annotated_filename,
        "fields": fields
    })


# ===============================
# SAVE RECORD
# ===============================

@app.route("/save", methods=["POST"])
def save():

    data = request.json

    row = [
        data.get("name", ""),
        data.get("designation", ""),
        data.get("phone", ""),
        data.get("email", ""),
        data.get("website", ""),
        data.get("address", "")
    ]

    saved_records.append(row)

    return jsonify({"status": "saved"})


# ===============================
# EXPORT CSV
# ===============================

@app.route("/export_csv")
def export_csv():

    if not saved_records:
        return "No records found", 400

    filename = f"business_cards_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    filepath = os.path.join(EXPORT_FOLDER, filename)

    with open(filepath, "w", newline="", encoding="utf-8") as f:

        writer = csv.writer(f)

        writer.writerow([
            "Name",
            "Designation",
            "Phone",
            "Email",
            "Website",
            "Address"
        ])

        for row in saved_records:
            writer.writerow(row)

    return send_file(filepath, as_attachment=True)


# ===============================
# RUN SERVER
# ===============================

if __name__ == "__main__":
    app.run(debug=True)