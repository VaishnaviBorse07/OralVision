"""
Recommendation Engine for OralVision
Generates rich clinical recommendations, follow-up dates, nearest cancer centres,
and cessation resources based on risk assessment.
"""
from datetime import date, timedelta
from typing import Optional


# ── State → Nearest Tata Memorial / Regional Cancer Centre mapping ────────────
_STATE_CANCER_CENTRES = {
    "Maharashtra":      "Tata Memorial Hospital, Mumbai (022-24177000)",
    "Gujarat":          "Gujarat Cancer Research Institute, Ahmedabad (079-26856000)",
    "Karnataka":        "Kidwai Memorial Institute of Oncology, Bengaluru (080-28398000)",
    "Tamil Nadu":       "Cancer Institute (WIA), Chennai (044-22350131)",
    "West Bengal":      "Chittaranjan National Cancer Institute, Kolkata (033-23213575)",
    "Delhi":            "AIIMS Cancer Centre, New Delhi (011-26588500)",
    "Andhra Pradesh":   "Basavatarakam Indo-American Cancer Hospital, Hyderabad (040-23551235)",
    "Telangana":        "MNJ Institute of Oncology, Hyderabad (040-23320741)",
    "Kerala":           "Regional Cancer Centre, Thiruvananthapuram (0471-2442541)",
    "Rajasthan":        "SMS Cancer Hospital, Jaipur (0141-2518501)",
    "Uttar Pradesh":    "King George's Medical University, Lucknow (0522-2258754)",
    "Madhya Pradesh":   "M.P. State Cancer Institute, Jabalpur (0761-2421427)",
    "Bihar":            "Mahavir Cancer Institute, Patna (0612-2281901)",
    "Odisha":           "Acharya Harihar Regional Cancer Centre, Cuttack (0671-2304540)",
    "Punjab":           "Government Medical College Cancer Centre, Amritsar (0183-2401609)",
    "Haryana":          "Civil Hospital Cancer Unit, Rohtak (01262-285673)",
    "Jharkhand":        "Rajendra Institute of Medical Sciences, Ranchi (0651-2545595)",
    "Assam":            "B. Borooah Cancer Institute, Guwahati (0361-2471095)",
    "Chhattisgarh":     "CIMS Hospital, Bilaspur (07752-410900)",
    "Himachal Pradesh": "IGMC Cancer Ward, Shimla (0177-2804251)",
    "Goa":              "Goa Medical College Oncology, Panaji (0832-2458727)",
    "Uttarakhand":      "All India Institute of Medical Sciences (AIIMS), Rishikesh (0135-2462954)",
    "Jammu & Kashmir":  "Government Medical College, Jammu (0191-2572443)",
    "Sikkim":           "STNM Hospital Cancer Unit, Gangtok (03592-202340)",
    "Tripura":          "ILS Hospitals, Agartala (0381-2411900)",
    "Manipur":          "Regional Institute of Medical Sciences, Imphal (0385-2411700)",
    "Meghalaya":        "Civil Hospital Cancer Unit, Shillong (0364-2223286)",
    "Arunachal Pradesh":"District Hospital Cancer Unit, Itanagar (0360-2244710)",
    "Nagaland":         "Naga Hospital Authority Cancer Unit, Kohima (0370-2291590)",
    "Mizoram":          "Civil Hospital Cancer Unit, Aizawl (0389-2322644)",
}

_DEFAULT_CENTRE = "Nearest Government District Cancer Centre / NPCDCS facility"


def get_recommendations(
    risk: str,
    confidence: float,
    age: int,
    tobacco_usage: bool,
    tobacco_type: str = "None",
    model_based: bool = False,
    state: str = "Maharashtra",
    engine: str = "heuristic",
) -> dict:
    """
    Returns comprehensive structured recommendations.

    Returns:
        {
            "recommendation":     str,
            "urgency":            str,   # URGENT / FOLLOW_UP / ROUTINE
            "alerts":             list[str],
            "hygiene_tips":       list[str],
            "referral_required":  bool,
            "next_followup_date": str,   # ISO date or description
            "nearest_center":     str,
            "cessation_helpline": str,
        }
    """
    today = date.today()
    alerts = []
    tips   = []

    # ── Nearest cancer centre by state ────────────────────────────────────────
    nearest_center = _STATE_CANCER_CENTRES.get(state, _DEFAULT_CENTRE)
    cessation_helpline = "iQuit: 1800-11-2356 (toll-free) | mCessation: SMS QUIT to 011-22901701"

    # ── Risk-specific recommendation, urgency, and follow-up ─────────────────
    if risk == "High":
        recommendation = (
            "⚠️ HIGH RISK DETECTED. Immediate referral to an oncologist or oral surgeon "
            "is critical. Do not delay — biopsy may be required within 48 hours. "
            f"Refer patient to {nearest_center}. "
            "Advise complete cessation of tobacco and alcohol immediately."
        )
        urgency            = "URGENT"
        referral           = True
        followup_date      = (today + timedelta(days=2)).isoformat()
        tips = [
            "Stop all tobacco and betel nut use TODAY — further exposure accelerates risk.",
            "Do not consume alcohol.",
            "Maintain oral hygiene with antiseptic chlorhexidine mouthwash.",
            f"Go to {nearest_center} within 48 hours.",
            "Document lesion: note size, color (red/white), location, and duration.",
            "Contact Ayushman Bharat (PMJAY) helpline 14555 for free cancer treatment coverage.",
        ]

    elif risk == "Medium":
        recommendation = (
            "⚠️ MEDIUM RISK. Follow-up oral screening required within 2 weeks. "
            "Monitor for changes in lesion size, color, texture, or pain. "
            "Reduce tobacco use immediately and schedule a clinical examination."
        )
        urgency            = "FOLLOW_UP"
        referral           = False
        followup_date      = (today + timedelta(weeks=2)).isoformat()
        tips = [
            "Reduce or completely eliminate tobacco and pan masala use now.",
            f"Schedule follow-up appointment at {nearest_center} within 2 weeks.",
            "Watch for warning signs: red/white patches, non-healing sores, pain, difficulty swallowing.",
            "Gargle with warm salt water twice daily for any existing mouth sores.",
            "Call iQuit on 1800-11-2356 (toll-free) for tobacco cessation support.",
            "Maintain good oral hygiene — brush twice daily with fluoride toothpaste.",
        ]

    else:  # Low
        recommendation = (
            "✅ LOW RISK. No immediate clinical intervention required. "
            "Continue annual oral health screening and maintain good oral hygiene. "
            "Any new sores or patches lasting more than 2 weeks must be evaluated."
        )
        urgency            = "ROUTINE"
        referral           = False
        followup_date      = (today + timedelta(days=365)).isoformat()
        tips = [
            "Brush teeth twice daily with fluoride toothpaste.",
            "Rinse mouth with clean water after every meal.",
            "Avoid tobacco, pan masala, and gutkha — risk increases with duration of use.",
            "Eat a balanced diet rich in fruits, vegetables, and antioxidants.",
            "Schedule annual oral screening at your nearest PHC or dental camp.",
            "See a doctor immediately if any mouth sore persists beyond 2 weeks.",
        ]

    # ── Additional alert flags ─────────────────────────────────────────────────
    if risk == "High":
        alerts.append("🚨 HIGH RISK — Specialist referral alert triggered.")

    if tobacco_usage and risk in ("High", "Medium"):
        t_name = tobacco_type.title() if tobacco_type and tobacco_type.lower() != "none" else "Tobacco"
        alerts.append(
            f"🚬 {t_name} use significantly elevates oral cancer risk 6–10×. "
            f"Cessation counselling is mandatory — call 1800-11-2356."
        )

    if age >= 60 and risk == "High":
        alerts.append(
            "👴 Age ≥ 60 with HIGH risk: HEIGHTENED priority — refer within 24 hours, "
            "not 48. Risk of rapid progression is elevated."
        )
    elif age >= 60 and risk == "Medium":
        alerts.append(
            "👴 Age ≥ 60 with MEDIUM risk: Earlier follow-up recommended within 1 week."
        )

    if confidence >= 0.88 and risk == "High":
        alerts.append(
            f"🔴 Very high confidence ({int(confidence * 100)}%) — strong malignancy signal. "
            f"Biopsy referral should be expedited."
        )
    elif confidence >= 0.72 and risk == "High":
        alerts.append(
            f"🔴 High confidence ({int(confidence * 100)}%) — lesion characteristics concerning."
        )

    tobacco_lower = tobacco_type.lower() if tobacco_type else "none"
    if tobacco_lower in ("gutka", "khaini", "mawa", "pan masala"):
        alerts.append(
            f"⚠️ Smokeless tobacco ({tobacco_type}) causes submucous fibrosis and leukoplakia — "
            f"pre-cancerous conditions requiring clinical monitoring."
        )
    elif tobacco_lower == "bidi":
        alerts.append(
            "⚠️ Bidi smoking is 3× more carcinogenic than cigarettes for oral cancer. "
            "Immediate cessation is critical."
        )

    # Engine info alert
    engine_labels = {
        "local_densenet":  "Local DenseNet121 CNN model (on-device image analysis)",
        "gemini_enhanced": "DenseNet121 + Gemini 1.5 Flash (multimodal AI + enhancement)",
        "gemini":          "Gemini 1.5 Flash multimodal vision model",
        "heuristic":       "Clinical risk heuristic (age + tobacco factors) — upload image for CNN analysis",
    }
    alerts.append(f"🤖 Engine: {engine_labels.get(engine, engine)}")

    return {
        "recommendation":     recommendation,
        "urgency":            urgency,
        "alerts":             alerts,
        "hygiene_tips":       tips,
        "referral_required":  referral,
        "next_followup_date": followup_date,
        "nearest_center":     nearest_center,
        "cessation_helpline": cessation_helpline,
    }
