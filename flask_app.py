import os
import base64
import cv2
import numpy as np
from flask import Flask, render_template, request, jsonify, send_from_directory

from application.cv.quality import validate_image_quality
from application.cv.preprocess import preprocess_light, preprocess_aggressive
from application.ocr.engine import extract_text
from application.nlp.ner import extract_entities
from application.export.csv_writer import append_to_csv
from application.export.vcard_writer import generate_vcard_content
from application.export.csv_writer import append_to_csv, is_duplicate


app = Flask(__name__)

VCARD_FOLDER = "outputs/vcards"
os.makedirs(VCARD_FOLDER, exist_ok=True)


# =============================
# HELPER FUNCTIONS (MATCH STREAMLIT)
# =============================

def is_usable(ocr):
    return ocr["confidence"] >= 40 and len(ocr["text"].strip()) >= 10


def run_pipeline(img):

    ok, _ = validate_image_quality(img)
    if not ok:
        return None, None

    ocr = extract_text(img)

    if not is_usable(ocr):
        ocr = extract_text(preprocess_light(img))

    if not is_usable(ocr):
        ocr = extract_text(preprocess_aggressive(img))

    entities = extract_entities(
        ocr["text"],
        ocr.get("lines", [])
    )

    return entities, ocr


def draw_bounding_boxes(image, ocr_data, entities):

    img_copy = image.copy()
    n = len(ocr_data["text"])

    for i in range(n):

        word = ocr_data["text"][i].strip()

        try:
            conf = int(float(ocr_data["conf"][i]))
        except:
            continue

        if not word or conf < 40:
            continue

        x = ocr_data["left"][i]
        y = ocr_data["top"][i]
        w = ocr_data["width"][i]
        h = ocr_data["height"][i]

        color = (200, 200, 200)  # default gray

        if entities.get("Name") and word.lower() in entities["Name"].lower():
            color = (0, 255, 0)

        elif entities.get("Phone") and word in entities["Phone"]:
            color = (255, 0, 0)

        elif entities.get("Email") and word.lower() in entities["Email"].lower():
            color = (255, 0, 255)

        elif entities.get("Address") and word.lower() in entities["Address"].lower():
            color = (0, 165, 255)

        cv2.rectangle(img_copy, (x, y), (x + w, y + h), color, 2)

    return img_copy


# =============================
# HOME
# =============================

@app.route("/")
def home():
    return render_template("index.html")


# =============================
# EXTRACT
# =============================

@app.route("/extract", methods=["POST"])
def extract():

    data = request.get_json()

    if not data or "image" not in data:
        return jsonify({"error": "No image"}), 400

    image_data = data["image"].split(",")[1]

    image_bytes = base64.b64decode(image_data)
    np_arr = np.frombuffer(image_bytes, np.uint8)
    image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    # RUN FULL PIPELINE (LIKE STREAMLIT)
    entities, ocr = run_pipeline(image)

    if entities is None or ocr is None:
        return jsonify({"error": "Image quality too poor."})

    # DRAW BOUNDING BOXES
    annotated = draw_bounding_boxes(
        image,
        ocr["data"],
        entities
    )

    # CONVERT TO BASE64
    _, buffer = cv2.imencode(".png", annotated)
    annotated_base64 = base64.b64encode(buffer).decode("utf-8")
    annotated_base64 = "data:image/png;base64," + annotated_base64

    return jsonify({
        "annotated": annotated_base64,
        "fields": entities
    })


# =============================
# SAVE
# =============================



@app.route("/save", methods=["POST"])
def save():

    record = request.get_json()

    if not record:
        return jsonify({"success": False})

    duplicate_type = is_duplicate(record)

    if duplicate_type:
        return jsonify({
            "success": False,
            "duplicate": duplicate_type
        })

    # Save CSV
    append_to_csv(record)

    # Generate vCard
    vcard_content = generate_vcard_content(record)

    safe_name = record.get("Name", "contact").replace(" ", "_")
    filename = f"{safe_name}.vcf"
    file_path = os.path.join(VCARD_FOLDER, filename)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(vcard_content)

    return jsonify({
        "success": True,
        "vcard": f"/download_vcard/{filename}"
    })

# =============================
# DOWNLOAD VCARD
# =============================

@app.route("/download_vcard/<filename>")
def download_vcard(filename):
    return send_from_directory(VCARD_FOLDER, filename, as_attachment=True)


# =============================
# RUN
# =============================

if __name__ == "__main__":
    app.run(debug=True)