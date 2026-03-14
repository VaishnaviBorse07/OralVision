from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.models.screening import FactScreening, DimPatient, DimGeography, DimRiskAssessment, ScreeningStatus, RiskLevel
from app.schemas.screening import ScreeningResponse, UpdateScreeningRequest
from app.routers.auth import require_admin
from app.models.user import User
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/screenings", tags=["Screenings"])

# Maps URL param values (case-insensitive) to RiskLevel enum
_RISK_MAP = {
    "high": RiskLevel.high,
    "medium": RiskLevel.medium,
    "low": RiskLevel.low,
}

# Maps URL param values (case-insensitive) to ScreeningStatus enum
_STATUS_MAP = {
    "pending": ScreeningStatus.pending,
    "reviewed": ScreeningStatus.reviewed,
}

@router.get("", response_model=List[ScreeningResponse])
def list_screenings(
    risk: Optional[str] = None,
    status: Optional[str] = None,
    village: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    query = (
        db.query(FactScreening)
        .join(DimRiskAssessment, FactScreening.dim_risk_assessment_id == DimRiskAssessment.id)
        .join(DimGeography, FactScreening.dim_geography_id == DimGeography.id)
        .join(DimPatient, FactScreening.dim_patient_id == DimPatient.id)
    )
    if risk:
        risk_enum = _RISK_MAP.get(risk.lower())
        if risk_enum is None:
            raise HTTPException(status_code=400, detail=f"Invalid risk value: '{risk}'. Must be High, Medium, or Low.")
        query = query.filter(DimRiskAssessment.risk_level == risk_enum)
    if status:
        status_enum = _STATUS_MAP.get(status.lower())
        if status_enum is None:
            raise HTTPException(status_code=400, detail=f"Invalid status value: '{status}'. Must be 'Pending' or 'Reviewed'.")
        query = query.filter(FactScreening.status == status_enum)
    if village:
        query = query.filter(DimGeography.village == village)
    return query.order_by(FactScreening.created_at.desc()).offset(skip).limit(limit).all()

@router.get("/{screening_id}", response_model=ScreeningResponse)
def get_screening(screening_id: int, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    s = db.query(FactScreening).filter(FactScreening.id == screening_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Screening not found")
    return s

@router.patch("/{screening_id}", response_model=ScreeningResponse)
def update_screening(
    screening_id: int,
    update: UpdateScreeningRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    s = db.query(FactScreening).filter(FactScreening.id == screening_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Screening not found")
    if update.status:
        s.status = update.status
    if update.notes is not None:
        s.notes = update.notes
    db.commit()
    db.refresh(s)
    return s
