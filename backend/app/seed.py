"""
Seed script: Creates demo users and 30 dummy screenings across Marathwada villages.
Run: python -m app.seed
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta, timezone
import random
from app.core.database import SessionLocal, init_db
from app.models.user import User, UserRole
from app.models.screening import FactScreening, DimRiskAssessment, DimGeography, DimPatient, DimHabits, TobaccoType, RiskLevel, ScreeningStatus, Gender
from app.core.security import hash_password

VILLAGES = [
    "Aurangabad", "Nanded", "Latur", "Osmanabad", "Beed",
    "Hingoli", "Parbhani", "Jalna", "Solapur", "Ambajogai", "Pune",
    "Mumbai", "Nagpur", "Nashik", "Thane", "Kolhapur"
]

RISK_LEVELS = [RiskLevel.high, RiskLevel.medium, RiskLevel.low]
RISK_WEIGHTS = [0.3, 0.4, 0.3]

def seed():
    init_db()
    db = SessionLocal()

    # Clear existing data
    db.query(FactScreening).delete()
    db.query(DimPatient).delete()
    db.query(DimGeography).delete()
    db.query(DimRiskAssessment).delete()
    db.query(DimHabits).delete()
    db.query(User).delete()
    db.commit()

    # Create admin user
    admin = User(
        name="Dr. Priya Sharma",
        email="admin@oralvision.ai",
        password_hash=hash_password("admin123"),
        role=UserRole.admin,
    )
    # Create clinic worker
    worker = User(
        name="Rahul Deshmukh",
        email="worker@oralvision.ai",
        password_hash=hash_password("worker123"),
        role=UserRole.clinic_worker,
    )
    db.add_all([admin, worker])
    db.commit()
    print("Users created: admin@oralvision.ai / admin123")

    # Create 35 dummy screenings over last 7 days
    screenings = []
    for i in range(35):
        risk = random.choices(RISK_LEVELS, weights=RISK_WEIGHTS)[0]
        days_ago = random.randint(0, 6)
        created = datetime.now(timezone.utc) - timedelta(days=days_ago, hours=random.randint(0, 12))
        confidence = random.uniform(0.61, 0.95) if risk == RiskLevel.high else \
                     random.uniform(0.35, 0.65) if risk == RiskLevel.medium else \
                     random.uniform(0.10, 0.34)
                     
        vname = random.choice(VILLAGES)
        
        # Dimensions
        dim_geo = db.query(DimGeography).filter_by(village=vname).first()
        if not dim_geo:
            dim_geo = DimGeography(village=vname)
            db.add(dim_geo)
            db.commit()
            db.refresh(dim_geo)

        dim_patient = DimPatient(
            patient_id_masked=f"OV-{random.randint(1000, 9999)}",
            age=random.randint(25, 75),
            gender=random.choice([Gender.male, Gender.female, Gender.other])
        )
        db.add(dim_patient)
        
        tobacco_type = random.choice([TobaccoType.gutka, TobaccoType.bidi, TobaccoType.none, TobaccoType.cigarette])
        dim_habits = DimHabits(primary_tobacco_type=tobacco_type)
        db.add(dim_habits)
        
        dim_risk = DimRiskAssessment(
            risk_level=risk,
            confidence_score=round(confidence, 2),
            clinical_explanation="Referred to district hospital." if risk == RiskLevel.high and random.random() > 0.5 else None
        )
        db.add(dim_risk)
        db.commit()
        db.refresh(dim_patient)
        db.refresh(dim_habits)
        db.refresh(dim_risk)

        screenings.append(FactScreening(
            dim_patient_id=dim_patient.id,
            dim_geography_id=dim_geo.id,
            dim_habits_id=dim_habits.id,
            dim_risk_assessment_id=dim_risk.id,
            image_url=None,
            status=random.choice([ScreeningStatus.pending, ScreeningStatus.pending, ScreeningStatus.reviewed]),
            created_at=created,
        ))

    db.add_all(screenings)
    db.commit()
    print(f"{len(screenings)} screenings seeded across {len(VILLAGES)} villages.")
    db.close()

if __name__ == "__main__":
    seed()

