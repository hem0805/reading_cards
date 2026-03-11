import cv2
import numpy as np


def blur_score(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return cv2.Laplacian(gray, cv2.CV_64F).var()


def brightness_score(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return float(np.mean(gray))


def contrast_score(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return float(np.std(gray))


def validate_image_quality(img):
    blur = blur_score(img)
    bright = brightness_score(img)
    contrast = contrast_score(img)

    issues = {}
    if blur < 70:
        issues["blur"] = "low"
    if contrast < 30:
        issues["contrast"] = "low"
    if bright < 50:
        issues["brightness"] = "dark"
    elif bright > 220:
        issues["brightness"] = "bright"

    # Reject ONLY if unusable
    if blur < 25 or bright < 25 or bright > 245:
        return False, {
            "status": "rejected",
            "metrics": {"blur": blur, "brightness": bright, "contrast": contrast}
        }

    return True, {
        "status": "accepted_with_warnings" if issues else "accepted",
        "issues": issues,
        "metrics": {"blur": blur, "brightness": bright, "contrast": contrast}
    }