from flask import Flask, render_template, request, jsonify, send_file
import os
import csv
import cv2
from datetime import datetime
import sys

from application.ocr.engine import extract_text
from application.nlp.ner import extract_entities
from application.cv.annotate import draw_boxes
from flask import url_for 

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def base_path():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.abspath(".")



app = Flask(__name__, static_folder=resource_path("static"), template_folder=resource_path("templates"))

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
OUTPUT_FOLDER = os.path.join(BASE_DIR, "static", "outputs")
EXPORT_FOLDER = os.path.join(BASE_DIR, "exports")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
os.makedirs(EXPORT_FOLDER, exist_ok=True)


# in-memory storage for saved records
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


    # build safe filename
    name, ext = os.path.splitext(file.filename)

    if ext == "":
        ext = ".jpg"

    filename = datetime.now().strftime("%Y%m%d%H%M%S") + "_" + name + ext

    filepath = os.path.join(UPLOAD_FOLDER, filename)

    file.save(filepath)


    # read uploaded image
    image = cv2.imread(filepath)

    if image is None:
        return jsonify({"error": "Image could not be read"}), 500


    # OCR
    ocr_result = extract_text(image)

    text = ocr_result["text"]
    lines = ocr_result["lines"]


    # NLP extraction
    fields = extract_entities(text, lines)


    # draw bounding boxes
    # draw bounding boxes
    annotated = draw_boxes(image, ocr_result["data"])

    annotated_filename = f"annotated_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
    annotated_path = os.path.join(OUTPUT_FOLDER, annotated_filename)

    # Save annotated image
    success = cv2.imwrite(annotated_path, annotated)

    if not success:
        return jsonify({"error": "Failed to save annotated image"}), 500

    annotated_url = f"/static/outputs/{annotated_filename}"

    return jsonify({
        "annotated_image": annotated_url,
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

    try:

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

    except Exception as e:
        return str(e), 500


# ===============================
# RUN SERVER
# ===============================

if __name__ == "__main__":
    app.run(debug=True)