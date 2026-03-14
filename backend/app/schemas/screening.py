from pydantic import BaseModel, field_validator, ConfigDict
from typing import Optional, List
from datetime import datetime
from enum import Enum


class RiskLevel(str, Enum):
    high = "High"
    medium = "Medium"
    low = "Low"


class ScreeningStatus(str, Enum):
    pending = "Pending"
    reviewed = "Reviewed"


class PredictResponse(BaseModel):
    risk: str
    confidence: float
    clinical_explanation: str = ""
    screening_id: int
    patient_id: str
    village: str
    state: str = ""
    message: str = ""
    recommendation: str = ""
    urgency: str = "ROUTINE"
    alerts: List = []
    hygiene_tips: List = []
    referral_required: bool = False
    model_based: bool = False


class ScreeningResponse(BaseModel):
    id: int
    patient_id: str
    age: int
    gender: str = ""
    tobacco_usage: bool = False
    primary_tobacco_type: str = "None"
    village: str = ""
    state: str = ""
    district: str = ""
    risk: str
    confidence: float
    clinical_explanation: Optional[str] = None
    image_url: Optional[str] = None
    status: str
    notes: Optional[str] = None
    created_at: datetime

    @field_validator("risk", mode="before")
    @classmethod
    def coerce_risk(cls, v):
        if hasattr(v, "value"):
            return v.value
        return str(v)

    @field_validator("status", mode="before")
    @classmethod
    def coerce_status(cls, v):
        if hasattr(v, "value"):
            return v.value
        return str(v)

    @field_validator("gender", mode="before")
    @classmethod
    def coerce_gender(cls, v):
        if v is None:
            return ""
        if hasattr(v, "value"):
            return v.value
        return str(v)

    @field_validator("primary_tobacco_type", mode="before")
    @classmethod
    def coerce_tobacco(cls, v):
        if v is None:
            return "None"
        if hasattr(v, "value"):
            return v.value
        return str(v)

    # clinical_explanation can come from DimRiskAssessment via FactScreening property
    @field_validator("clinical_explanation", mode="before")
    @classmethod
    def coerce_explanation(cls, v):
        return v  # allow None

    model_config = ConfigDict(from_attributes=True)


class UpdateScreeningRequest(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None
