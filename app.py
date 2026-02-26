import streamlit as st
import cv2
import numpy as np
import pandas as pd
import os

from application.cv.quality import validate_image_quality
from application.cv.preprocess import preprocess_light, preprocess_aggressive
from application.ocr.engine import extract_text
from application.nlp.ner import extract_entities
from application.export.csv_writer import append_to_csv, get_csv_path


# -------------------------------------------------
# Helper: decide whether OCR output is usable
# -------------------------------------------------
def is_ocr_usable(ocr_result):
    return (
        ocr_result["confidence"] >= 40 and
        len(ocr_result["text"].strip()) >= 10
    )


# -------------------------------------------------
# Page configuration
# -------------------------------------------------
st.set_page_config(
    page_title="Business Card OCR",
    page_icon="📇",
    layout="centered"
)

st.title("📇 Business Card Scanner")
st.caption(
    "Original-first OCR • Line-wise text • Intelligent preprocessing fallback"
)

# -------------------------------------------------
# Image input
# -------------------------------------------------
mode = st.radio(
    "Select input method",
    ["Upload Image", "Camera"],
    horizontal=True
)

image = None

if mode == "Upload Image":
    uploaded_file = st.file_uploader(
        "Upload a business card image",
        type=["jpg", "jpeg", "png"]
    )
    if uploaded_file:
        image = cv2.imdecode(
            np.frombuffer(uploaded_file.read(), np.uint8),
            cv2.IMREAD_COLOR
        )
else:
    camera_image = st.camera_input("Capture business card")
    if camera_image:
        image = cv2.imdecode(
            np.frombuffer(camera_image.read(), np.uint8),
            cv2.IMREAD_COLOR
        )

# -------------------------------------------------
# Main pipeline
# -------------------------------------------------
if image is not None:
    st.image(image, channels="BGR", caption="Input Image")

    if st.button("🔍 Extract Information", use_container_width=True):

        # 1️⃣ Image quality check (soft)
        ok, quality = validate_image_quality(image)
        if not ok:
            st.error("Image quality is too poor for OCR.")
            st.stop()

        if quality["status"] == "accepted_with_warnings":
            st.warning("⚠️ Image quality is low — OCR confidence may be affected")

        # 2️⃣ FIRST PASS — ORIGINAL IMAGE
        ocr = extract_text(image)

        # 3️⃣ SECOND PASS — LIGHT PREPROCESS
        if not is_ocr_usable(ocr):
            st.info("Retrying OCR with light preprocessing…")
            processed = preprocess_light(image)
            ocr = extract_text(processed)

        # 4️⃣ THIRD PASS — AGGRESSIVE PREPROCESS
        if not is_ocr_usable(ocr):
            st.info("Retrying OCR with aggressive preprocessing…")
            processed = preprocess_aggressive(image)
            ocr = extract_text(processed)

        # 5️⃣ Entity extraction (LINE-AWARE)
        entities = extract_entities(
            ocr["text"],
            ocr.get("lines", [])
        )
        entities["OCR_Confidence"] = ocr["confidence"]

        # 6️⃣ Save to CSV
        append_to_csv(entities)

        # -------------------------------------------------
        # Results UI
        # -------------------------------------------------
        st.success("✅ Extraction complete")

        st.metric("OCR Confidence", f"{ocr['confidence']}%")
        st.write(f"OCR Engine Used: **{ocr.get('engine', 'unknown')}**")

        # Arrow-safe table (Field → Value)
        df = pd.DataFrame(
            list(entities.items()),
            columns=["Field", "Value"]
        ).astype(str)

        st.subheader("📇 Extracted Information")
        st.table(df)

        # -------------------------------------------------
        # Raw OCR output (line by line)
        # -------------------------------------------------
        st.subheader("📄 Raw OCR Text (Line by Line)")

        if ocr.get("lines"):
            for idx, line in enumerate(ocr["lines"], start=1):
                st.text(f"{idx:02d}. {line}")
        else:
            st.info("No readable text lines detected.")

        # -------------------------------------------------
        # CSV Download
        # -------------------------------------------------
        csv_path = get_csv_path()
        if os.path.exists(csv_path):
            with open(csv_path, "rb") as f:
                st.download_button(
                    label="⬇️ Download Extracted CSV",
                    data=f,
                    file_name="business_cards.csv",
                    mime="text/csv",
                    use_container_width=True
                )