import sys
sys.path.insert(0, r"E:\OralVision\backend")
from main import app
from fastapi.testclient import TestClient

client = TestClient(app)
try:
    print("Dashboard:", client.get("/dashboard/stats").status_code)
except Exception as e:
    print("Dashboard Error:", e)

try:
    print("Screenings:", client.get("/screenings").status_code)
except Exception as e:
    print("Screenings Error:", e)

print("Done")
