"""
screening.py — Pan-India Enterprise Star Schema for OralVision
Dimensional data model optimized for Power BI / analytical queries.

Fact table: FactScreening
Dimensions: DimGeography, DimPatient, DimHabits, DimRiskAssessment

Design principles:
  - All PII fields hold pre-masked values (masked before insert via security.py)
  - Enum columns use native string values for cross-DB portability
  - Indexes on high-cardinality join columns for query performance
  - Soft-delete pattern via status field (never hard-delete screening records)
"""

from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime,
    Text, Enum, ForeignKey, Index,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum


# ── Enumerations ────────────────────────────────────────────────────────────────

class TobaccoType(str, enum.Enum):
    """Primary smokeless / smoke tobacco habits prevalent in rural India."""
    none       = "None"
    gutka      = "Gutka"
    khaini     = "Khaini"
    mawa       = "Mawa"
    bidi       = "Bidi"
    cigarette  = "Cigarette"
    pan_masala = "Pan Masala"
    other      = "Other"


class RiskLevel(str, enum.Enum):
    high   = "High"
    medium = "Medium"
    low    = "Low"


class ScreeningStatus(str, enum.Enum):
    pending  = "Pending"
    reviewed = "Reviewed"


class Gender(str, enum.Enum):
    male          = "Male"
    female        = "Female"
    other         = "Other"
    not_disclosed = "Not Disclosed"


# ── Dimension: Geography ─────────────────────────────────────────────────────────

class DimGeography(Base):
    """
    Pan-India geography dimension.
    Supports district-level and village-level granularity for heatmap analytics.
    """
    __tablename__ = "dim_geography"

    id       = Column(Integer, primary_key=True, index=True)
    state    = Column(String(100), nullable=False, default="Maharashtra")
    district = Column(String(100), nullable=False, default="")
    pincode  = Column(String(10),  nullable=True)
    village  = Column(String(150), nullable=False)

    # Composite unique — same village name may appear in different districts
    __table_args__ = (
        Index("ix_geo_state_district_village", "state", "district", "village"),
    )

    screenings = relationship("FactScreening", back_populates="geography")


# ── Dimension: Patient ───────────────────────────────────────────────────────────

class DimPatient(Base):
    """
    Patient dimension — all PII is pre-masked before insert (see security.mask_patient_id).
    Gender is stored for gender-stratified analytics reported to NPCDCS.
    """
    __tablename__ = "dim_patients"

    id                = Column(Integer, primary_key=True, index=True)
    patient_id_masked = Column(String(50), index=True, nullable=False)
    age               = Column(Integer, nullable=False)
    gender            = Column(Enum(Gender), nullable=False, default=Gender.not_disclosed)

    screenings = relationship("FactScreening", back_populates="patient")


# ── Dimension: Habits ────────────────────────────────────────────────────────────

class DimHabits(Base):
    """
    Habit dimension capturing the primary tobacco type for each screening.
    Enables tobacco-stratified risk analytics for ASHA worker counselling reports.
    """
    __tablename__ = "dim_habits"

    id                  = Column(Integer, primary_key=True, index=True)
    primary_tobacco_type = Column(
        Enum(TobaccoType),
        nullable=False,
        default=TobaccoType.none,
    )

    screenings = relationship("FactScreening", back_populates="habits")


# ── Dimension: Risk Assessment ───────────────────────────────────────────────────

class DimRiskAssessment(Base):
    """
    Stores the AI-generated risk assessment output.
    clinical_explanation holds the Gemini multimodal response text.
    """
    __tablename__ = "dim_risk_assessments"

    id                   = Column(Integer, primary_key=True, index=True)
    risk_level           = Column(Enum(RiskLevel), nullable=False, index=True)
    confidence_score     = Column(Float, nullable=False)
    clinical_explanation = Column(Text, nullable=True)

    screenings = relationship("FactScreening", back_populates="risk_assessment")


# ── Fact: Screening ──────────────────────────────────────────────────────────────

class FactScreening(Base):
    """
    Central fact table. Each row = one patient screening event.

    Foreign keys reference all four dimensions.
    image_url stores the path of the uploaded oral cavity image.
    status tracks clinical review lifecycle (Pending → Reviewed).
    clinician_notes holds post-review doctor annotations.
    """
    __tablename__ = "fact_screenings"

    id                     = Column(Integer, primary_key=True, index=True)
    dim_patient_id         = Column(Integer, ForeignKey("dim_patients.id"),         nullable=False)
    dim_geography_id       = Column(Integer, ForeignKey("dim_geography.id"),        nullable=False)
    dim_habits_id          = Column(Integer, ForeignKey("dim_habits.id"),           nullable=False)
    dim_risk_assessment_id = Column(Integer, ForeignKey("dim_risk_assessments.id"), nullable=False)

    image_url       = Column(String(500), nullable=True)
    status          = Column(Enum(ScreeningStatus), default=ScreeningStatus.pending, nullable=False)
    clinician_notes = Column(Text, nullable=True)
    created_at      = Column(
        DateTime(timezone=True),
        default=func.now(),
        server_default=func.now(),
        nullable=False,
    )

    # ORM relationships
    patient         = relationship("DimPatient",        back_populates="screenings")
    geography       = relationship("DimGeography",      back_populates="screenings")
    habits          = relationship("DimHabits",         back_populates="screenings")
    risk_assessment = relationship("DimRiskAssessment", back_populates="screenings")

    # ── Convenience properties for backwards-compatible response schemas ──────

    @property
    def patient_id(self) -> str:
        return self.patient.patient_id_masked

    @property
    def age(self) -> int:
        return self.patient.age

    @property
    def gender(self) -> str:
        return self.patient.gender.value if hasattr(self.patient.gender, "value") else str(self.patient.gender)

    @property
    def tobacco_usage(self) -> bool:
        """True for any non-None tobacco type (backwards compatibility)."""
        return self.habits.primary_tobacco_type != TobaccoType.none

    @property
    def primary_tobacco_type(self) -> str:
        return self.habits.primary_tobacco_type.value if hasattr(self.habits.primary_tobacco_type, "value") else str(self.habits.primary_tobacco_type)

    @property
    def village(self) -> str:
        return self.geography.village

    @property
    def state(self) -> str:
        return self.geography.state

    @property
    def district(self) -> str:
        return self.geography.district

    @property
    def risk(self):
        return self.risk_assessment.risk_level

    @property
    def confidence(self) -> float:
        return self.risk_assessment.confidence_score

    @property
    def notes(self) -> str:
        return self.clinician_notes

    @notes.setter
    def notes(self, value: str):
        self.clinician_notes = value

    @property
    def clinical_explanation(self) -> str:
        """Retrieve the Gemini AI explanation from the linked DimRiskAssessment."""
        return self.risk_assessment.clinical_explanation if self.risk_assessment else None
