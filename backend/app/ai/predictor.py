"""
OralVision Predictor — Multi-Engine Risk Assessment
Execution order:
  1. Local DenseNet121 (offline, always free)
  2. Gemini 1.5 Flash (enhances explanation if API key available)
  3. Clinical Heuristic (final fallback — no image, no API key)
"""

import base64
import json
import logging
import re
from typing import Optional

from app.ai.recommendations import get_recommendations

logger = logging.getLogger(__name__)

# ── Gemini system prompt ──────────────────────────────────────────────────────
_SYSTEM_PROMPT = """You are an expert oncology triaging AI assistant integrated into OralVision,
a rural oral cancer early detection platform deployed in India for ASHA workers and clinicians.

Your task is to analyze an oral cavity image along with patient metadata and an initial AI
risk assessment, then produce a REFINED structured clinical risk assessment.

STRICT RULES:
1. Respond ONLY with a single valid JSON object — no markdown, no explanation, no extra text.
2. The JSON must match this EXACT schema:
   {
     "risk_level": "High" | "Medium" | "Low",
     "confidence_score": <float between 0.0 and 1.0>,
     "clinical_explanation": "<2-4 sentence clinical rationale>"
   }
3. Base risk_level on BOTH the image AND the patient metadata:
   - HIGH: visible suspicious lesions (erythroplakia, leukoplakia, ulcers, masses, submucous fibrosis,
     persistent red/white patches), especially with tobacco use or age > 55.
   - MEDIUM: borderline lesions, hyperkeratosis, mild inflammatory changes, or strong risk factor profile
     (heavy tobacco + age 40–55) with no clear lesion visible.
   - LOW: normal mucosa appearance, no visible lesions, minimal or no risk factors.
4. confidence_score must reflect genuine certainty. Never return exactly 1.0 or 0.0.
5. clinical_explanation must be medically precise and actionable:
   - Reference specific visual findings (color, location, size, texture)
   - Mention tobacco-type risk if relevant (e.g., gutka causes submucous fibrosis)
   - Recommend the specific next step (biopsy, 2-week follow-up, annual screening)
6. NEVER include patient names or identifiable information in the explanation.
"""

_ENHANCEMENT_PROMPT = """You are an expert oncology AI assistant for OralVision.
The local DenseNet121 model has already assessed this image.

Local model result:
  - Risk Level: {risk_level}
  - Raw Score: {raw_score}
  - Local Explanation: {local_explanation}

Patient Metadata:
  - Age: {age} years
  - State: {state}
  - District: {district}
  - Primary tobacco habit: {tobacco_display}

Your task: Review BOTH the image AND the local model's assessment, then produce a REFINED
clinical explanation that is more medically specific and actionable.

STRICT RULES:
1. Respond ONLY with a single valid JSON object — no markdown, no extra text.
2. Schema:
   {{
     "risk_level": "High" | "Medium" | "Low",
     "confidence_score": <float 0.01-0.99>,
     "clinical_explanation": "<2-4 sentence refined clinical rationale>"
   }}
3. You may adjust the risk_level and confidence if your visual analysis disagrees with the local model.
4. clinical_explanation must reference: specific visual findings, tobacco type, age risk, next step.
5. NEVER include identifiable information.
"""


def _heuristic_score(age: int, tobacco_type: str) -> dict:
    """
    NPCDCS-based clinical heuristic fallback when no image and no API key.
    """
    tobacco_heavy = tobacco_type.strip().lower() not in ("none", "", "false", "0")
    score = 0.0

    if age >= 60:
        score += 0.35
    elif age >= 45:
        score += 0.22
    elif age >= 30:
        score += 0.12
    else:
        score += 0.04

    # Tobacco type risk adjustment
    tobacco_lower = tobacco_type.strip().lower()
    if tobacco_lower in ("gutka", "khaini", "mawa", "pan masala"):
        score += 0.38   # smokeless tobacco — higher OSCC risk
    elif tobacco_lower in ("bidi",):
        score += 0.35   # bidi more carcinogenic than cigarette
    elif tobacco_lower in ("cigarette",):
        score += 0.28
    elif tobacco_heavy:
        score += 0.25

    score = min(score, 0.97)

    if score >= 0.60:
        risk = "High"
        explanation = (
            f"High clinical risk profile: age {age} with {tobacco_type or 'tobacco'} use are "
            f"significant independent risk factors for oral squamous cell carcinoma. "
            f"Image analysis unavailable — immediate clinical visual inspection is required. "
            f"Refer to District Hospital for physical examination."
        )
    elif score >= 0.35:
        risk = "Medium"
        explanation = (
            f"Moderate risk profile based on age ({age} years) and tobacco history ({tobacco_type or 'None'}). "
            f"Follow-up oral examination recommended within 2–4 weeks. "
            f"Upload an oral image for AI-enhanced analysis."
        )
    else:
        risk = "Low"
        explanation = (
            f"Low clinical risk based on age ({age} years) and reported habits. "
            f"No major risk factors identified at this time. "
            f"Continue routine annual screening and maintain good oral hygiene."
        )

    return {
        "risk_level":           risk,
        "confidence_score":     round(score, 4),
        "clinical_explanation": explanation,
    }


def _parse_gemini_response(text: str) -> Optional[dict]:
    """Extract and validate JSON from Gemini response (handles markdown fences)."""
    text = re.sub(r"```(?:json)?", "", text).strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group())
            except json.JSONDecodeError:
                return None
        else:
            return None

    required = {"risk_level", "confidence_score", "clinical_explanation"}
    if not required.issubset(data.keys()):
        logger.warning("Gemini response missing required fields: %s", data.keys())
        return None

    if data["risk_level"] not in ("High", "Medium", "Low"):
        logger.warning("Invalid risk_level from Gemini: %s", data["risk_level"])
        return None

    try:
        data["confidence_score"] = round(
            max(0.01, min(0.99, float(data["confidence_score"]))), 4
        )
    except (TypeError, ValueError):
        data["confidence_score"] = 0.50

    return data


async def predict_risk(
    image_bytes: Optional[bytes],
    age: int,
    tobacco_type: str,
    patient_id: str,
    state: str = "Maharashtra",
    district: str = "",
) -> dict:
    """
    Multi-engine risk prediction entry point.

    Flow:
      1. Local DenseNet121 — if model file exists and image provided
      2. Gemini 1.5 Flash  — if API key set; used to refine DenseNet result OR
                             perform standalone vision analysis
      3. Clinical Heuristic — final fallback when no image / API key
    """
    from app.core.config import get_settings
    settings = get_settings()

    final_result = None
    model_based  = False
    engine_used  = "heuristic"

    tobacco_display = tobacco_type if tobacco_type else "None"
    tobacco_str     = str(tobacco_type).strip() if tobacco_type else "none"

    # ── Engine 1: Local DenseNet121 ──────────────────────────────────────────
    if image_bytes:
        try:
            from app.ai.local_predictor import predict_local
            local_result = predict_local(image_bytes, age=age, tobacco_type=tobacco_str)
            if local_result:
                final_result = local_result
                model_based  = True
                engine_used  = "local_densenet"
                logger.info(
                    "DenseNet121 prediction: risk=%s confidence=%.4f raw=%.4f patient=%s",
                    local_result["risk_level"],
                    local_result["confidence_score"],
                    local_result.get("raw_score", 0),
                    patient_id,
                )
        except Exception as e:
            logger.warning("Local DenseNet inference failed: %s", e)

    # ── Engine 2: Gemini 1.5 Flash ───────────────────────────────────────────
    if settings.google_api_key and image_bytes:
        try:
            import google.generativeai as genai

            genai.configure(api_key=settings.google_api_key)

            # If local model ran, use enhancement prompt; else use standalone prompt
            if final_result and engine_used == "local_densenet":
                prompt_text = _ENHANCEMENT_PROMPT.format(
                    risk_level       = final_result["risk_level"],
                    raw_score        = final_result.get("raw_score", "N/A"),
                    local_explanation= final_result["clinical_explanation"],
                    age              = age,
                    state            = state,
                    district         = district or "Not provided",
                    tobacco_display  = tobacco_display,
                )
                system_instr = "You are an expert oncology AI. Output only valid JSON."
            else:
                prompt_text = (
                    f"Patient Metadata:\n"
                    f"  - Age: {age} years\n"
                    f"  - State: {state}\n"
                    f"  - District: {district or 'Not provided'}\n"
                    f"  - Primary tobacco habit: {tobacco_display}\n\n"
                    f"Analyze the oral cavity image and provide the risk assessment JSON."
                )
                system_instr = _SYSTEM_PROMPT

            gemini_model = genai.GenerativeModel(
                model_name          = "gemini-1.5-flash",
                system_instruction  = system_instr,
                generation_config   = genai.GenerationConfig(
                    temperature      = 0.15,
                    top_p            = 0.85,
                    max_output_tokens= 600,
                ),
            )

            b64_image = base64.b64encode(image_bytes).decode("utf-8")
            response  = await gemini_model.generate_content_async([
                {"mime_type": "image/jpeg", "data": b64_image},
                prompt_text,
            ])

            gemini_result = _parse_gemini_response(response.text.strip())
            if gemini_result:
                final_result = gemini_result
                model_based  = True
                engine_used  = "gemini_enhanced" if engine_used == "local_densenet" else "gemini"
                logger.info(
                    "Gemini prediction: risk=%s confidence=%.4f engine=%s patient=%s",
                    gemini_result["risk_level"],
                    gemini_result["confidence_score"],
                    engine_used,
                    patient_id,
                )
            else:
                logger.warning("Gemini response parse failed — keeping DenseNet result.")

        except Exception as e:
            logger.warning("Gemini API call failed: %s — using local/heuristic result.", e)

    # ── Engine 3: Clinical Heuristic fallback ────────────────────────────────
    if final_result is None:
        final_result = _heuristic_score(age, tobacco_str)
        engine_used  = "heuristic"
        logger.info(
            "Heuristic fallback: risk=%s confidence=%.4f patient=%s",
            final_result["risk_level"],
            final_result["confidence_score"],
            patient_id,
        )

    risk        = final_result["risk_level"]
    confidence  = final_result["confidence_score"]
    explanation = final_result["clinical_explanation"]

    # ── Enrich with structured recommendations ───────────────────────────────
    tobacco_bool = tobacco_str.lower() not in ("none", "", "false", "0")
    rec = get_recommendations(
        risk          = risk,
        confidence    = confidence,
        age           = age,
        tobacco_usage = tobacco_bool,
        tobacco_type  = tobacco_str,
        model_based   = model_based,
        state         = state,
        engine        = engine_used,
    )

    return {
        "risk":                  risk,
        "confidence":            confidence,
        "clinical_explanation":  explanation,
        "recommendation":        rec["recommendation"],
        "urgency":               rec["urgency"],
        "alerts":                rec["alerts"],
        "hygiene_tips":          rec["hygiene_tips"],
        "referral_required":     rec["referral_required"],
        "next_followup_date":    rec["next_followup_date"],
        "nearest_center":        rec["nearest_center"],
        "cessation_helpline":    rec["cessation_helpline"],
        "model_based":           model_based,
        "engine":                engine_used,
    }
