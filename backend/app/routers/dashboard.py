from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import get_db
from app.models.screening import FactScreening, DimRiskAssessment, DimGeography, DimPatient, DimHabits, TobaccoType, RiskLevel, ScreeningStatus
from app.routers.auth import require_admin
from app.models.user import User
from datetime import date, timedelta, datetime

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

MARATHWADA_VILLAGES = {
    "Aurangabad": (19.8762, 75.3433),
    "Nanded": (19.1383, 77.3210),
    "Latur": (18.4088, 76.5604),
    "Osmanabad": (18.1867, 76.0411),
    "Beed": (18.9890, 75.7601),
    "Hingoli": (19.7177, 77.1498),
    "Parbhani": (19.2698, 76.7755),
    "Jalna": (19.8333, 75.8833),
    "Solapur": (17.6599, 75.9064),
    "Ambajogai": (18.7323, 76.3814),
}

@router.get("/stats")
def get_dashboard_stats(db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    today = date.today()
    today_start = datetime(today.year, today.month, today.day)
    today_end = today_start + timedelta(days=1)

    # Total screenings today
    today_total = db.query(func.count(FactScreening.id)).filter(
        FactScreening.created_at >= today_start,
        FactScreening.created_at < today_end,
    ).scalar() or 0

    # All time counts
    total = db.query(func.count(FactScreening.id)).scalar() or 0
    high = db.query(func.count(FactScreening.id)).join(DimRiskAssessment, FactScreening.dim_risk_assessment_id == DimRiskAssessment.id).filter(DimRiskAssessment.risk_level == RiskLevel.high).scalar() or 0
    medium = db.query(func.count(FactScreening.id)).join(DimRiskAssessment, FactScreening.dim_risk_assessment_id == DimRiskAssessment.id).filter(DimRiskAssessment.risk_level == RiskLevel.medium).scalar() or 0
    low = db.query(func.count(FactScreening.id)).join(DimRiskAssessment, FactScreening.dim_risk_assessment_id == DimRiskAssessment.id).filter(DimRiskAssessment.risk_level == RiskLevel.low).scalar() or 0
    pending = db.query(func.count(FactScreening.id)).filter(FactScreening.status == ScreeningStatus.pending).scalar() or 0
    avg_confidence = db.query(func.avg(DimRiskAssessment.confidence_score)).join(FactScreening, FactScreening.dim_risk_assessment_id == DimRiskAssessment.id).scalar() or 0.0

    # Risk distribution for pie chart
    risk_distribution = [
        {"name": "High Risk", "value": high, "color": "#ef4444"},
        {"name": "Medium Risk", "value": medium, "color": "#f59e0b"},
        {"name": "Low Risk", "value": low, "color": "#10b981"},
    ]

    # Screenings over last 7 days (line chart)
    screenings_over_time = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        day_start = datetime(day.year, day.month, day.day)
        day_end = day_start + timedelta(days=1)
        count = db.query(func.count(FactScreening.id)).filter(
            FactScreening.created_at >= day_start,
            FactScreening.created_at < day_end,
        ).scalar() or 0
        # Also count high risk for that day
        high_count = db.query(func.count(FactScreening.id)).join(DimRiskAssessment).filter(
            FactScreening.created_at >= day_start,
            FactScreening.created_at < day_end,
            DimRiskAssessment.risk_level == RiskLevel.high,
        ).scalar() or 0
        screenings_over_time.append({
            "date": day.strftime("%b %d"),
            "screenings": count,
            "high_risk": high_count,
        })

    # Village-wise high-risk bar chart
    village_stats_raw = (
        db.query(DimGeography.village, func.count(FactScreening.id).label("count"))
        .select_from(FactScreening)
        .join(DimGeography)
        .join(DimRiskAssessment)
        .filter(DimRiskAssessment.risk_level == RiskLevel.high)
        .group_by(DimGeography.village)
        .all()
    )
    village_high_risk = [{"village": v, "high_risk": c} for v, c in village_stats_raw]

    # Heatmap data
    all_villages = (
        db.query(DimGeography.village, func.count(FactScreening.id).label("total"))
        .select_from(FactScreening)
        .join(DimGeography)
        .group_by(DimGeography.village)
        .all()
    )
    high_villages = (
        db.query(DimGeography.village, func.count(FactScreening.id).label("high_count"))
        .select_from(FactScreening)
        .join(DimGeography)
        .join(DimRiskAssessment)
        .filter(DimRiskAssessment.risk_level == RiskLevel.high)
        .group_by(DimGeography.village)
        .all()
    )
    high_map = {v: c for v, c in high_villages}

    heatmap_data = []
    for village, total_count in all_villages:
        coords = MARATHWADA_VILLAGES.get(village)
        if coords:
            hc = high_map.get(village, 0)
            heatmap_data.append({
                "village": village,
                "lat": coords[0],
                "lng": coords[1],
                "total": total_count,
                "high_count": hc,
                "risk_density": round(hc / max(total_count, 1), 2),
            })

    # ── Age-group risk breakdown ───────────────────────────────────────────────
    # NOTE: Each sub-query is built independently to avoid broken join state
    # that results from chaining .join() on an already-joined query object.
    age_groups = [
        ("Under 30", 0, 29),
        ("30–45", 30, 45),
        ("45–60", 46, 60),
        ("Over 60", 61, 200),
    ]
    age_group_risk = []
    for label, age_min, age_max in age_groups:
        # Independent query for total screenings in this age group
        total_group = (
            db.query(func.count(FactScreening.id))
            .join(DimPatient, FactScreening.dim_patient_id == DimPatient.id)
            .filter(DimPatient.age >= age_min, DimPatient.age <= age_max)
            .scalar() or 0
        )
        # Independent query for high-risk screenings in this age group
        high_group = (
            db.query(func.count(FactScreening.id))
            .join(DimPatient, FactScreening.dim_patient_id == DimPatient.id)
            .join(DimRiskAssessment, FactScreening.dim_risk_assessment_id == DimRiskAssessment.id)
            .filter(
                DimPatient.age >= age_min,
                DimPatient.age <= age_max,
                DimRiskAssessment.risk_level == RiskLevel.high,
            )
            .scalar() or 0
        )
        age_group_risk.append({
            "group": label,
            "total": total_group,
            "high_risk": high_group,
        })

    # ── Tobacco vs non-tobacco risk (using DimHabits — tobacco_usage moved from DimPatient) ─
    tobacco_high = (
        db.query(func.count(FactScreening.id))
        .join(DimHabits, FactScreening.dim_habits_id == DimHabits.id)
        .join(DimRiskAssessment, FactScreening.dim_risk_assessment_id == DimRiskAssessment.id)
        .filter(DimHabits.primary_tobacco_type != TobaccoType.none, DimRiskAssessment.risk_level == RiskLevel.high)
        .scalar() or 0
    )
    no_tobacco_high = (
        db.query(func.count(FactScreening.id))
        .join(DimHabits, FactScreening.dim_habits_id == DimHabits.id)
        .join(DimRiskAssessment, FactScreening.dim_risk_assessment_id == DimRiskAssessment.id)
        .filter(DimHabits.primary_tobacco_type == TobaccoType.none, DimRiskAssessment.risk_level == RiskLevel.high)
        .scalar() or 0
    )
    tobacco_total = (
        db.query(func.count(FactScreening.id))
        .join(DimHabits, FactScreening.dim_habits_id == DimHabits.id)
        .filter(DimHabits.primary_tobacco_type != TobaccoType.none)
        .scalar() or 0
    )
    no_tobacco_total = (
        db.query(func.count(FactScreening.id))
        .join(DimHabits, FactScreening.dim_habits_id == DimHabits.id)
        .filter(DimHabits.primary_tobacco_type == TobaccoType.none)
        .scalar() or 0
    )
    tobacco_risk = [
        {
            "name": "Tobacco Users",
            "total": tobacco_total,
            "high_risk": tobacco_high,
            "pct": round(tobacco_high / max(tobacco_total, 1) * 100, 1),
        },
        {
            "name": "Non-Tobacco",
            "total": no_tobacco_total,
            "high_risk": no_tobacco_high,
            "pct": round(no_tobacco_high / max(no_tobacco_total, 1) * 100, 1),
        },
    ]

    # ── Recent activity feed (last 10 screenings) ─────────────────────────────
    recent_rows = (
        db.query(FactScreening)
        .join(DimRiskAssessment, FactScreening.dim_risk_assessment_id == DimRiskAssessment.id)
        .join(DimPatient, FactScreening.dim_patient_id == DimPatient.id)
        .join(DimGeography, FactScreening.dim_geography_id == DimGeography.id)
        .join(DimHabits, FactScreening.dim_habits_id == DimHabits.id)
        .order_by(FactScreening.created_at.desc())
        .limit(10)
        .all()
    )
    recent_screenings = []
    for s in recent_rows:
        recent_screenings.append({
            "id": s.id,
            "patient_id": s.patient_id,
            "village": s.village,
            "state": s.state,
            "primary_tobacco_type": s.primary_tobacco_type,
            "age": s.age,
            "risk": s.risk.value if hasattr(s.risk, "value") else str(s.risk),
            "confidence": round(s.confidence, 3),
            "status": s.status.value if hasattr(s.status, "value") else str(s.status),
            "created_at": s.created_at.isoformat() if s.created_at else None,
        })

    return {
        "summary": {
            "today_total": today_total,
            "total": total,
            "high": high,
            "medium": medium,
            "low": low,
            "pending_reviews": pending,
            "avg_confidence": round(float(avg_confidence), 3),
            "high_pct": round(high / max(total, 1) * 100, 1),
            "medium_pct": round(medium / max(total, 1) * 100, 1),
            "low_pct": round(low / max(total, 1) * 100, 1),
        },
        "risk_distribution": risk_distribution,
        "screenings_over_time": screenings_over_time,
        "village_high_risk": village_high_risk,
        "heatmap": heatmap_data,
        "age_group_risk": age_group_risk,
        "tobacco_risk": tobacco_risk,
        "recent_screenings": recent_screenings,
    }
