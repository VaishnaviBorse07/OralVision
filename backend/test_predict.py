import sys
import os

sys.path.insert(0, r"E:\OralVision\backend")
from main import app
from fastapi.testclient import TestClient
from app.routers.auth import get_current_user
from app.models.user import User

async def override_get_current_user():
    return User(id=1, email="test@test.com", role="admin")

app.dependency_overrides[get_current_user] = override_get_current_user

client = TestClient(app)

with open("predict_log.txt", "w", encoding="utf-8") as f:
    f.write(f"Testing /predict...\n")
    try:
        response = client.post("/predict", data={
            "patient_id": "TEST_123",
            "age": 45,
            "gender": "Male",
            "state": "Maharashtra",
            "district": "Pune",
            "village": "Wakad",
            "tobacco_type": "Gutka"
        })
        f.write(f"Predict Status: {response.status_code}\n")
        f.write(f"Response: {response.text}\n")
    except Exception as e:
        f.write(f"Exception: {e}\n")
