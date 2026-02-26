import streamlit as st
import cv2
import numpy as np
import pandas as pd

from application.cv.quality import validate_image_quality
from application.cv.preprocess import preprocess_light, preprocess_aggressive
from application.ocr.engine import extract_text
from application.nlp.ner import extract_entities
from application.export.csv_writer import append_to_csv


# ----------------------------------
# Helpers
# ----------------------------------
def is_ocr_usable(ocr):
    return (
        ocr["confidence"] >= 40 and
        len(ocr["text"].strip()) >= 10
    )


# ----------------------------------
# Page setup
# ----------------------------------
st.set_page_config(
    page_title="Business Card OCR",
    page_icon="📇",
    layout="centered"
)

st.title("📇 Real-World Business Card Scanner")
st.caption("Line-aware OCR • Layout preserved • Cleaner entity extraction")

# ----------------------------------
# Image input
# ----------------------------------
mode = st.radio("Input method", ["Upload Image", "Camera"], horizontal=True)
image = None

if mode == "Upload Image":
    file = st.file_uploader("Upload business card", ["jpg", "jpeg", "png"])
    if file:
        image = cv2.imdecode(
            np.frombuffer(file.read(), np.uint8),
            cv2.IMREAD_COLOR
        )
else:
    cam = st.camera_input("Capture business card")
    if cam:
        image = cv2.imdecode(
            np.frombuffer(cam.read(), np.uint8),
            cv2.IMREAD_COLOR
        )

# ----------------------------------
# Processing pipeline
# ----------------------------------
if image is not None:
    st.image(image, channels="BGR", caption="Input Image")

    if st.button("🔍 Extract Information", use_container_width=True):

        # 1️⃣ Quality check (soft)
        ok, quality = validate_image_quality(image)
        if not ok:
            st.error("Image too poor to process")
            st.stop()

        if quality["status"] == "accepted_with_warnings":
            st.warning("⚠️ Image quality is low — OCR confidence may be affected")

        # 2️⃣ FIRST PASS — ORIGINAL IMAGE (most reliable)
        ocr = extract_text(image)

        # 3️⃣ SECOND PASS — LIGHT PREPROCESS
        if not is_ocr_usable(ocr):
            st.info("Retrying with light preprocessing…")
            processed = preprocess_light(image)
            ocr = extract_text(processed)

        # 4️⃣ THIRD PASS — AGGRESSIVE PREPROCESS (last resort)
        if not is_ocr_usable(ocr):
            st.info("Retrying with aggressive preprocessing…")
            processed = preprocess_aggressive(image)
            ocr = extract_text(processed)

        # 5️⃣ NER (line-aware)
        entities = extract_entities(
            ocr["text"],
            ocr.get("lines", [])
        )
        entities["OCR_Confidence"] = ocr["confidence"]

        # 6️⃣ Save to CSV
        append_to_csv(entities)

        # ----------------------------------
        # Results
        # ----------------------------------
        st.success("✅ Extraction complete")

        st.metric("OCR Confidence", f"{ocr['confidence']}%")
        st.write(f"OCR Engine Used: **{ocr.get('engine', 'unknown')}**")

        # Arrow-safe table
        df = pd.DataFrame(
            list(entities.items()),
            columns=["Field", "Value"]
        ).astype(str)

        st.subheader("📇 Extracted Information")
        st.table(df)

        # ----------------------------------
        # Raw OCR output (LINE BY LINE)
        # ----------------------------------
        st.subheader("📄 Raw OCR Text (Line by Line)")

        if ocr.get("lines"):
            for idx, line in enumerate(ocr["lines"], start=1):
                st.text(f"{idx:02d}. {line}")
        else:
            st.info("No readable text lines detected.")