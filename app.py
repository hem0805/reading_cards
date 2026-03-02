import streamlit as st
import cv2
import numpy as np
import pandas as pd
import hashlib
import os

from application.cv.quality import validate_image_quality
from application.cv.preprocess import preprocess_light, preprocess_aggressive
from application.ocr.engine import extract_text
from application.nlp.ner import extract_entities
from application.export.csv_writer import append_to_csv, get_csv_path


# -------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------
st.set_page_config(
    page_title="Business Card Scanner",
    page_icon="📇",
    layout="wide"
)

# -------------------------------------------------
# CUSTOM STYLING + LOADER
# -------------------------------------------------
st.markdown("""
<style>

section.main > div {
    padding-top: 1rem;
}

/* Title */
.app-title {
    text-align: center;
    font-size: 32px;
    font-weight: 700;
    margin-bottom: 25px;
}

/* Loader */
.loader {
  border: 6px solid #f3f3f3;
  border-top: 6px solid #4A6CF7;
  border-radius: 50%;
  width: 50px;
  height: 50px;
  animation: spin 1s linear infinite;
  margin: auto;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.loader-container {
  text-align: center;
  padding: 40px;
}

/* Button */
.stButton>button {
    background-color: #4A6CF7;
    color: white;
    border-radius: 8px;
    height: 42px;
    font-weight: 600;
    border: none;
}

.stButton>button:hover {
    background-color: #3b5ae0;
}

</style>
""", unsafe_allow_html=True)

st.markdown('<div class="app-title">📇 Business Card Scanner</div>',
            unsafe_allow_html=True)

# -------------------------------------------------
# SESSION STATE
# -------------------------------------------------
if "processed_hash" not in st.session_state:
    st.session_state.processed_hash = None

if "image" not in st.session_state:
    st.session_state.image = None

if "ocr_data" not in st.session_state:
    st.session_state.ocr_data = None

if "current_record" not in st.session_state:
    st.session_state.current_record = None


# -------------------------------------------------
# HELPERS
# -------------------------------------------------
def compute_hash(img):
    return hashlib.md5(img.tobytes()).hexdigest()


def is_usable(ocr):
    return ocr["confidence"] >= 40 and len(ocr["text"].strip()) >= 10


def draw_bounding_boxes(image, ocr_data):
    img_copy = image.copy()
    n = len(ocr_data["text"])

    for i in range(n):
        word = ocr_data["text"][i].strip()

        try:
            conf = int(float(ocr_data["conf"][i]))
        except:
            continue

        if word and conf > 40:
            x = ocr_data["left"][i]
            y = ocr_data["top"][i]
            w = ocr_data["width"][i]
            h = ocr_data["height"][i]

            cv2.rectangle(
                img_copy,
                (x, y),
                (x + w, y + h),
                (0, 255, 0),
                2
            )

    return img_copy


def run_pipeline(img):

    ok, _ = validate_image_quality(img)
    if not ok:
        st.error("Image quality too poor.")
        return None, None

    ocr = extract_text(img)

    if not is_usable(ocr):
        ocr = extract_text(preprocess_light(img))

    if not is_usable(ocr):
        ocr = extract_text(preprocess_aggressive(img))

    entities = extract_entities(ocr["text"], ocr.get("lines", []))

    return entities, ocr


# -------------------------------------------------
# INPUT SECTION (CENTERED)
# -------------------------------------------------
center = st.columns([1, 2, 1])[1]

with center:

    mode = st.radio(
        "Select Input Method",
        ["Upload Image", "Camera"],
        horizontal=True
    )

    img = None

    if mode == "Upload Image":
        uploaded = st.file_uploader(
            "Upload Business Card",
            type=["jpg", "jpeg", "png"]
        )
        if uploaded:
            img = cv2.imdecode(
                np.frombuffer(uploaded.read(), np.uint8),
                cv2.IMREAD_COLOR
            )

    elif mode == "Camera":
        camera = st.camera_input("Capture Business Card")
        if camera:
            img = cv2.imdecode(
                np.frombuffer(camera.read(), np.uint8),
                cv2.IMREAD_COLOR
            )


# -------------------------------------------------
# AUTO EXTRACTION WITH ANIMATION
# -------------------------------------------------
if img is not None:

    img_hash = compute_hash(img)

    if img_hash != st.session_state.processed_hash:

        st.session_state.processed_hash = img_hash
        st.session_state.image = img

        loader = st.empty()

        loader.markdown("""
        <div class="loader-container">
        <div class="loader"></div>
        <p>Extracting business card details...</p>
        </div>
        """, unsafe_allow_html=True)

        entities, ocr = run_pipeline(img)

        loader.empty()

        st.session_state.current_record = entities
        st.session_state.ocr_data = ocr


# -------------------------------------------------
# RESULTS SECTION
# -------------------------------------------------
if st.session_state.current_record and st.session_state.image is not None:

    st.markdown("---")

    col1, col2 = st.columns([1.2, 1], gap="large")

    # LEFT: Annotated Image
    with col1:
        st.markdown("### Detected Text Regions")

        annotated = draw_bounding_boxes(
            st.session_state.image,
            st.session_state.ocr_data["data"]
        )

        st.image(
            annotated,
            channels="BGR",
            use_container_width=True
        )

    # RIGHT: Editable Fields
    with col2:
        st.markdown("### Extracted Details")

        name = st.text_input(
            "Name",
            st.session_state.current_record.get("Name", "")
        )

        designation = st.text_input(
            "Designation",
            st.session_state.current_record.get("Designation", "")
        )

        phone = st.text_input(
            "Phone",
            st.session_state.current_record.get("Phone", "")
        )

        email = st.text_input(
            "Email",
            st.session_state.current_record.get("Email", "")
        )

        website = st.text_input(
            "Website",
            st.session_state.current_record.get("Website", "")
        )

        address = st.text_area(
            "Address",
            st.session_state.current_record.get("Address", "")
        )

        if st.button("OK - Save Record", use_container_width=True):

            record = {
                "Name": name,
                "Designation": designation,
                "Phone": phone,
                "Email": email,
                "Website": website,
                "Address": address
            }

            append_to_csv(record)
            st.success("Record saved permanently to CSV!")


# -------------------------------------------------
# PREVIEW TABLE (NOT SAVED)
# -------------------------------------------------
if st.session_state.current_record:

    st.markdown("---")
    st.markdown("### Preview (Not Saved Until OK)")

    preview_df = pd.DataFrame([st.session_state.current_record])
    st.dataframe(preview_df, use_container_width=True)