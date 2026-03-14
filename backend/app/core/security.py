"""
security.py — Authentication, JWT, and DPDP/HIPAA PII Masking Utilities

Key exports:
  - verify_password / hash_password      — bcrypt password handling
  - create_access_token / decode_token   — JWT lifecycle
  - mask_patient_id(patient_id) -> str   — DPDP-compliant PII redaction
  - mask_pii(text) -> str                — Generic field scrubber hook
"""

import re
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
from app.core.config import get_settings

settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ── Password utilities ────────────────────────────────────────────────────────


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a stored bcrypt hash."""
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt."""
    return pwd_context.hash(password)


# ── JWT utilities ─────────────────────────────────────────────────────────────


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a signed JWT access token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.jwt_expire_minutes)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> Optional[dict]:
    """Decode and verify a JWT. Returns None on any failure."""
    try:
        return jwt.decode(
            token, settings.jwt_secret, algorithms=[settings.jwt_algorithm]
        )
    except JWTError:
        return None


# ── PII Masking — DPDP Act 2023 / HIPAA Safe Harbour compliant ───────────────


def mask_patient_id(patient_id: str) -> str:
    """
    Redact all but the last 4 characters of a patient identifier.

    DPDP/HIPAA compliance: the raw patient ID must never be stored in the
    database or passed to any external AI API. Only the masked token is stored.

    Examples:
        "PAT-20241012-RAMESH-9834" → "********************9834"
        "AB12"                     → "AB12"   (≤4 chars → unchanged)
        ""                         → ""

    The masked token is deterministic, so the same raw ID always produces the
    same masked token — enabling de-duplication without storing PII.
    """
    if not patient_id:
        return patient_id
    pid = patient_id.strip()
    if len(pid) <= 4:
        return pid
    return "*" * (len(pid) - 4) + pid[-4:]


def hash_patient_id(patient_id: str) -> str:
    """
    Return a one-way SHA-256 hex digest of the patient ID for use as a
    consistent pseudonymous key in analytics pipelines. The original ID
    cannot be reconstructed from this hash.
    """
    if not patient_id:
        return ""
    return hashlib.sha256(patient_id.strip().encode()).hexdigest()


def mask_pii(text: str) -> str:
    """
    Generic PII scrubber applied to free-text fields (village names, notes)
    before they reach AI APIs or are written to the database.

    Current rules:
      - Strip Indian mobile numbers: 10-digit numbers starting with 6-9
      - Strip Aadhaar-like 12-digit numeric patterns
      - Strip email addresses

    Extend this function with presidio or a custom NER model for production.
    """
    if not text:
        return text

    # Redact Indian mobile numbers (10 digits starting with 6–9)
    text = re.sub(r"\b[6-9]\d{9}\b", "***PHONE***", text)

    # Redact Aadhaar-style 12-digit numbers
    text = re.sub(r"\b\d{4}\s?\d{4}\s?\d{4}\b", "***AADHAAR***", text)

    # Redact email addresses
    text = re.sub(r"\b[\w.+-]+@[\w-]+\.\w{2,}\b", "***EMAIL***", text)

    return text
