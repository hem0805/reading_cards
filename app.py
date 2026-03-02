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
from application.export.csv_writer import append_to_csv, is_duplicate
from application.export.vcard_writer import save_vcard


# -------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------
st.set_page_config(
    page_title="Business Card Scanner",
    page_icon="📇",
    layout="wide"
)

st.markdown("<h2 style='text-align:center;'>📇 Business Card Scanner</h2>",
            unsafe_allow_html=True)


# -------------------------------------------------
# SESSION STATE
# -------------------------------------------------
if "processed_hash" not in st.session_state:
    st.session_state.processed_hash = None

if "current_record" not in st.session_state:
    st.session_state.current_record = None

if "ocr_data" not in st.session_state:
    st.session_state.ocr_data = None

if "image" not in st.session_state:
    st.session_state.image = None


# -------------------------------------------------
# HELPERS
# -------------------------------------------------
def compute_hash(img):
    return hashlib.md5(img.tobytes()).hexdigest()


def is_usable(ocr):
    return ocr["confidence"] >= 40 and len(ocr["text"].strip()) >= 10


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

        color = (200, 200, 200)  # Default Gray

        if entities.get("Name") and word.lower() in entities["Name"].lower():
            color = (0, 255, 0)  # Green

        elif entities.get("Phone") and word in entities["Phone"]:
            color = (255, 0, 0)  # Blue

        elif entities.get("Email") and word.lower() in entities["Email"].lower():
            color = (255, 0, 255)  # Purple

        elif entities.get("Address") and word.lower() in entities["Address"].lower():
            color = (0, 165, 255)  # Orange

        cv2.rectangle(img_copy, (x, y), (x + w, y + h), color, 2)

    return img_copy


# -------------------------------------------------
# INPUT SECTION
# -------------------------------------------------
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

else:
    camera = st.camera_input("Capture Business Card")
    if camera:
        img = cv2.imdecode(
            np.frombuffer(camera.read(), np.uint8),
            cv2.IMREAD_COLOR
        )


# -------------------------------------------------
# AUTO EXTRACTION
# -------------------------------------------------
if img is not None:

    img_hash = compute_hash(img)

    if img_hash != st.session_state.processed_hash:

        st.session_state.processed_hash = img_hash
        st.session_state.image = img

        with st.spinner("Extracting details..."):
            entities, ocr = run_pipeline(img)

        st.session_state.current_record = entities
        st.session_state.ocr_data = ocr


# -------------------------------------------------
# DISPLAY RESULTS
# -------------------------------------------------
if st.session_state.current_record and st.session_state.image is not None:

    col1, col2 = st.columns([1.2, 1], gap="large")

    # LEFT SIDE - Annotated Image
    with col1:

        annotated = draw_bounding_boxes(
            st.session_state.image,
            st.session_state.ocr_data["data"],
            st.session_state.current_record
        )

        st.image(
            annotated,
            channels="BGR",
            use_container_width=True
        )

    # RIGHT SIDE - Editable Fields
    with col2:

        st.subheader("Extracted Details")

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
                "Name": (name or "").strip(),
                "Designation": (designation or "").strip(),
                "Phone": (phone or "").strip(),
                "Email": (email or "").strip().lower(),
                "Website": (website or "").strip(),
                "Address": (address or "").strip()
            }

            duplicate_type = is_duplicate(record)

            if duplicate_type:

                if duplicate_type == "email":
                    st.warning("⚠ A contact with this email already exists.")

                elif duplicate_type == "phone":
                    st.warning("⚠ A contact with this phone already exists (no email provided).")

            else:
                append_to_csv(record)
                vcard_path = save_vcard(record)

                st.success("Record saved successfully!")

                with open(vcard_path, "rb") as f:
                    st.download_button(
                        label="📱 Download Contact (.vcf)",
                        data=f,
                        file_name=os.path.basename(vcard_path),
                        mime="text/vcard"
                    )

    # -------------------------------------------------
    # PREVIEW TABLE
    # -------------------------------------------------
    st.markdown("---")
    st.subheader("Preview (Not Saved Until OK)")

    preview_df = pd.DataFrame([st.session_state.current_record])
    st.dataframe(preview_df, use_container_width=True)