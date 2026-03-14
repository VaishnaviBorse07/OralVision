import os
import httpx
from fastapi import APIRouter, Depends, File, Form, UploadFile, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from app.core.database import get_db
from app.core.config import get_settings
from app.models.screening import (
    FactScreening, DimPatient, DimGeography, DimHabits, DimRiskAssessment,
    RiskLevel, ScreeningStatus, TobaccoType, Gender,
)
from app.ai.predictor import predict_risk
from app.core.security import mask_patient_id, mask_pii
from app.routers.auth import get_current_user
from app.models.user import User
import logging

router = APIRouter(tags=["Prediction"])
settings = get_settings()
logger = logging.getLogger(__name__)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _parse_tobacco_type(raw: str) -> TobaccoType:
    """Map a free-text tobacco string to TobaccoType enum (case-insensitive, forgiving)."""
    if not raw:
        return TobaccoType.none
    raw_lower = raw.strip().lower()
    for member in TobaccoType:
        if member.value.lower() == raw_lower or member.name.lower() == raw_lower:
            return member
    # Legacy boolean-string compatibility
    if raw_lower in ("true", "1", "yes"):
        return TobaccoType.other
    return TobaccoType.none


def _parse_gender(raw: str) -> Gender:
    if not raw:
        return Gender.not_disclosed
    for member in Gender:
        if member.value.lower() == raw.strip().lower():
            return member
    return Gender.not_disclosed


@router.post("/predict")
async def predict(
    patient_id: str = Form(...),
    age: int = Form(...),
    gender: str = Form(default="Not Disclosed"),
    state: str = Form(default="Maharashtra"),
    district: str = Form(default=""),
    village: str = Form(default=""),
    tobacco_type: str = Form(default="None"),
    tobacco_usage: Optional[str] = Form(default=None),
    image: UploadFile = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # ── Step 1: PII masking ─────────────────────────────────────────────────
    masked_patient_id = mask_patient_id(patient_id)
    clean_village = mask_pii(village or district or state)
    clean_state = mask_pii(state)
    clean_district = mask_pii(district)

    # ── Step 2: Read image ──────────────────────────────────────────────────
    image_bytes = None
    image_url = None
    if image and image.filename:
        image_bytes = await image.read()
        ext = os.path.splitext(image.filename)[1] or ".jpg"

        # Strip characters that are illegal in Windows filenames: * ? " < > | : \ /
        import re
        safe_id = re.sub(r'[\\/*?:"<>|\s]', "_", masked_patient_id)

        import time
        safe_name = f"{safe_id}_{int(time.time())}{ext}"
        file_path = os.path.join(UPLOAD_DIR, safe_name)
        with open(file_path, "wb") as f:
            f.write(image_bytes)
        image_url = f"/uploads/{safe_name}"

    # ── Step 3: Resolve tobacco type ─────────────────────────────────────────
    tobacco_enum = _parse_tobacco_type(tobacco_type)
    if tobacco_enum == TobaccoType.none and tobacco_usage is not None:
        tobacco_enum = _parse_tobacco_type(tobacco_usage)

    tobacco_bool = tobacco_enum != TobaccoType.none
    gender_enum = _parse_gender(gender)

    # ── Step 4: Multi-engine AI prediction ───────────────────────────────────
    # Pass tobacco_type as a STRING so Gemini/DenseNet get the actual type name
    result = await predict_risk(
        image_bytes=image_bytes,
        age=age,
        tobacco_type=tobacco_enum.value,   # e.g. "Gutka", "Bidi", "None"
        patient_id=patient_id,
        state=clean_state,
        district=clean_district,
    )
    risk_str = result["risk"]
    confidence = result["confidence"]
    clinical_explanation = result.get("clinical_explanation", "No explanation available.")

    risk_enum_map = {
        "High":   RiskLevel.high,
        "Medium": RiskLevel.medium,
        "Low":    RiskLevel.low,
    }
    risk_enum = risk_enum_map.get(risk_str, RiskLevel.medium)

    # ── Step 5: Insert into Star Schema ─────────────────────────────────────
    dim_geo = (
        db.query(DimGeography)
        .filter(
            DimGeography.state    == clean_state,
            DimGeography.district == clean_district,
            DimGeography.village  == clean_village,
        )
        .first()
    )
    if not dim_geo:
        dim_geo = DimGeography(
            state    = clean_state,
            district = clean_district,
            village  = clean_village,
        )
        db.add(dim_geo)
        db.flush()

    dim_patient = DimPatient(
        patient_id_masked = masked_patient_id,
        age               = age,
        gender            = gender_enum,
    )
    db.add(dim_patient)

    dim_habits = DimHabits(primary_tobacco_type=tobacco_enum)
    db.add(dim_habits)

    dim_risk = DimRiskAssessment(
        risk_level           = risk_enum,
        confidence_score     = confidence,
        clinical_explanation = clinical_explanation,
    )
    db.add(dim_risk)

    db.flush()

    fact_screening = FactScreening(
        dim_patient_id        = dim_patient.id,
        dim_geography_id      = dim_geo.id,
        dim_habits_id         = dim_habits.id,
        dim_risk_assessment_id= dim_risk.id,
        image_url             = image_url,
        status                = ScreeningStatus.pending,
    )
    db.add(fact_screening)
    db.commit()
    db.refresh(fact_screening)

    # ── Step 6: Webhook for high-risk cases ─────────────────────────────────
    message = ""
    if risk_str == "High" and settings.n8n_webhook_url:
        try:
            payload = {
                "screening_id":        fact_screening.id,
                "masked_patient_id":   masked_patient_id,
                "state":               clean_state,
                "village":             clean_village,
                "tobacco_type":        tobacco_enum.value,
                "clinical_explanation":clinical_explanation,
                "image_url":           image_url,
            }
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.post(settings.n8n_webhook_url, json=payload)
                message = (
                    "High risk alert sent to specialist."
                    if resp.status_code < 400
                    else "High risk detected. Alert delivery pending."
                )
        except Exception as e:
            logger.warning("n8n webhook failed: %s", e)
            message = "High risk detected. Alert queued."
    elif risk_str == "High":
        message = "High risk detected. Configure N8N_WEBHOOK_URL for specialist alerts."

    return {
        "risk":                risk_str,
        "confidence":          confidence,
        "clinical_explanation":clinical_explanation,
        "screening_id":        fact_screening.id,
        "patient_id":          patient_id,
        "village":             village or district or state,
        "state":               state,
        "message":             message,
        "recommendation":      result.get("recommendation", ""),
        "urgency":             result.get("urgency", "ROUTINE"),
        "alerts":              result.get("alerts", []),
        "hygiene_tips":        result.get("hygiene_tips", []),
        "referral_required":   result.get("referral_required", False),
        "model_based":         result.get("model_based", False),
        "engine":              result.get("engine", "heuristic"),
        "next_followup_date":  result.get("next_followup_date", ""),
        "nearest_center":      result.get("nearest_center", ""),
        "cessation_helpline":  result.get("cessation_helpline", ""),
    }
