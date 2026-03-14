"""
Local DenseNet121 Predictor for OralVision
Runs entirely on-device — no API key required.
Loads oral_cancer_model.h5 and classifies oral cavity images.

KEY DIAGNOSIS (confirmed by empirical testing):
  - The model was trained with class labels INVERTED relative to sigmoid output.
    i.e. raw_score ≈ P(normal), NOT P(cancer).
  - cancer_score = 1.0 - raw_score   ← always use this

  - The model has augmentation layers (RandomFlip, RandomRotation etc.) baked
    into the graph. During inference these must be suppressed by calling
    model(arr, training=False).

  - The model ALSO applies densenet.preprocess_input internally. Do NOT apply
    it again in Python — that causes double-normalisation and corrupts scores.

Scoring uses a COMPOSITE approach:
  - Image-derived cancer score contributes 70% of the final composite score
  - Clinical heuristic factors (age + tobacco type) contribute 30%
"""
import logging
import os
from functools import lru_cache
from io import BytesIO
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)

MODEL_PATH = os.path.join(os.path.dirname(__file__), "oral_cancer_model.h5")
IMG_SIZE   = (224, 224)

# Weight split: image model vs. clinical heuristic
_MODEL_WEIGHT     = 0.70
_HEURISTIC_WEIGHT = 0.30


@lru_cache(maxsize=1)
def _load_model():
    """Load Keras model once, cache it in memory."""
    if not os.path.exists(MODEL_PATH):
        logger.warning("oral_cancer_model.h5 not found at %s", MODEL_PATH)
        return None
    try:
        import tensorflow as tf                       # lazy import
        model = tf.keras.models.load_model(MODEL_PATH)
        logger.info("DenseNet121 oral cancer model loaded from %s", MODEL_PATH)
        return model
    except Exception as exc:
        logger.error("Failed to load DenseNet121 model: %s", exc)
        return None


def _clinical_heuristic_score(age: int, tobacco_type: str) -> float:
    """
    Return a normalised [0.0, 1.0] clinical risk score based on
    NPCDCS guidelines.
    """
    score = 0.0
    tobacco_lower = tobacco_type.strip().lower() if tobacco_type else "none"

    # Age contribution
    if age >= 60:
        score += 0.40
    elif age >= 45:
        score += 0.25
    elif age >= 30:
        score += 0.14
    else:
        score += 0.05

    # Tobacco type contribution
    if tobacco_lower in ("gutka", "khaini", "mawa", "pan masala"):
        score += 0.42   # smokeless tobacco — high OSCC risk
    elif tobacco_lower in ("bidi",):
        score += 0.38   # bidi more carcinogenic than cigarettes
    elif tobacco_lower in ("cigarette",):
        score += 0.30
    elif tobacco_lower not in ("none", "", "false", "0"):
        score += 0.25   # other tobacco

    return min(score, 0.97)


def predict_local(
    image_bytes: bytes,
    age: int = 40,
    tobacco_type: str = "none",
) -> Optional[dict]:
    """
    Run DenseNet121 inference on raw image bytes.

    IMPORTANT: raw_score from this model = P(normal).
    cancer_score = 1 - raw_score  is used for risk thresholding.

    Returns:
        {
          "risk_level": "High" | "Medium" | "Low",
          "confidence_score": float,      # 0.01–0.99
          "clinical_explanation": str,
          "raw_score": float,             # original sigmoid output
          "cancer_score": float,          # inverted: 1 - raw_score
          "composite_score": float,       # blended final score
        }
        or None on failure.
    """
    model = _load_model()
    if model is None:
        return None

    try:
        import tensorflow as tf
        from PIL import Image

        # ── Preprocess ───────────────────────────────────────────────────────
        # Do NOT call densenet.preprocess_input here — the model already does
        # it internally. Just resize to (224,224) and feed raw float32 pixels.
        img = Image.open(BytesIO(image_bytes)).convert("RGB").resize(IMG_SIZE)
        arr = np.array(img, dtype=np.float32)
        arr = np.expand_dims(arr, axis=0)

        # ── Inference ────────────────────────────────────────────────────────
        # Use training=False to suppress RandomFlip / RandomRotation / etc.
        raw_score = float(model(arr, training=False).numpy()[0][0])
        raw_score = max(0.01, min(0.99, raw_score))

        # ── Invert: raw_score = P(normal) → cancer_score = P(cancer) ─────────
        cancer_score = 1.0 - raw_score
        cancer_score = max(0.01, min(0.99, cancer_score))

        # ── Composite score: image + clinical heuristic ───────────────────────
        heuristic_score = _clinical_heuristic_score(age, tobacco_type)
        composite_score = (
            _MODEL_WEIGHT * cancer_score +
            _HEURISTIC_WEIGHT * heuristic_score
        )
        composite_score = max(0.01, min(0.99, composite_score))

        tobacco_display = tobacco_type.strip() if tobacco_type else "None"
        if tobacco_display.lower() in ("none", "", "false", "0"):
            tobacco_display = "None"

        # ── Risk thresholding on composite score ──────────────────────────────
        if composite_score >= 0.55:
            risk = "High"
            conf = composite_score
            explanation = (
                f"The DenseNet121 model detected high-probability malignant characteristics "
                f"(image cancer score {cancer_score:.2f}, composite {composite_score:.2f}). "
                f"Lesion patterns consistent with erythroplakia, leukoplakia, or submucous "
                f"fibrosis may be present. Patient risk profile: age {age}, "
                f"tobacco: {tobacco_display}. Immediate clinical evaluation is strongly advised."
            )
        elif composite_score >= 0.30:
            risk = "Medium"
            conf = composite_score
            explanation = (
                f"The DenseNet121 model detected borderline oral lesion features "
                f"(image cancer score {cancer_score:.2f}, composite {composite_score:.2f}). "
                f"Patient risk profile: age {age}, tobacco: {tobacco_display}. "
                f"Mild mucosal changes or early-stage lesions may be present. "
                f"Follow-up oral examination within 2–4 weeks is recommended."
            )
        else:
            risk = "Low"
            conf = 1.0 - composite_score   # confidence in absence of cancer
            explanation = (
                f"The DenseNet121 model found no strong malignant features "
                f"(image cancer score {cancer_score:.2f}, composite {composite_score:.2f}). "
                f"Patient: age {age}, tobacco: {tobacco_display}. "
                f"Oral mucosa appears within normal limits. Routine annual screening advised."
            )

        conf = max(0.01, min(0.99, conf))

        logger.info(
            "local_predictor: raw=%.4f cancer=%.4f heuristic=%.4f composite=%.4f risk=%s",
            raw_score, cancer_score, heuristic_score, composite_score, risk,
        )

        return {
            "risk_level":           risk,
            "confidence_score":     round(conf, 4),
            "clinical_explanation": explanation,
            "raw_score":            round(raw_score, 4),
            "cancer_score":         round(cancer_score, 4),
            "composite_score":      round(composite_score, 4),
        }

    except Exception as exc:
        logger.error("DenseNet121 inference failed: %s", exc)
        return None
