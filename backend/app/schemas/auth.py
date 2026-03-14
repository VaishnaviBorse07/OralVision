from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional
from enum import Enum

class UserRole(str, Enum):
    admin = "admin"
    clinic_worker = "clinic_worker"

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    name: str

class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    role: str

    model_config = ConfigDict(from_attributes=True)

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: UserRole = UserRole.clinic_worker
