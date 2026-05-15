🦷 OralVision — Multimodal AI for Oral Cancer Detection

An AI-powered oral cancer screening system designed for early detection in rural and low-resource healthcare environments. OralVision empowers frontline healthcare workers with real-time AI-assisted oral lesion analysis using mobile devices.

📌 Problem Statement

Oral cancer contributes to nearly one-third of all cancer cases in India. Early-stage detection can significantly improve survival rates, but most patients are diagnosed late due to the lack of affordable and accessible screening systems in rural areas.

OralVision addresses this challenge by providing:

📱 Mobile-first AI screening
🧠 Real-time oral lesion risk analysis
🏥 Automatic referral alerts
🌐 Offline-capable Progressive Web App (PWA)

The platform is designed especially for ASHA workers and community healthcare professionals.

✨ Features
📸 Capture oral lesion images directly from mobile devices
🔍 AI-powered lesion classification
🧠 Generative AI clinical summaries
📲 Offline-capable Progressive Web App (PWA)
🏥 Automatic hospital referral alerts
🌍 Multilingual-ready architecture
⚡ Real-time inference on low-end Android devices
🔐 Secure authentication & patient management
🏗️ System Architecture
🧠 AI Model Details
Component	Details
Architecture	DenseNet121 (Fine-Tuned)
Task	Multi-Class Image Classification
Classes	Low Risk / Medium Risk / High Risk
Framework	PyTorch
Input	Clinical Oral Cavity Images
Preprocessing	Resizing, Normalization, Augmentation
Deployment	ONNX Optimization for Mobile Inference
🛠️ Tech Stack
Layer	Technology
Frontend	React.js, PWA
Backend	FastAPI, Python
Deep Learning	PyTorch, torchvision
Generative AI	OpenAI API / Custom LLM
Database	PostgreSQL
Deployment	Docker, Uvicorn
Image Processing	OpenCV, Pillow
# 📁 Project Structure

```bash
OralVision/
│
├── backend/
│   ├── main.py
│   ├── routes/
│   │   ├── predict.py
│   │   ├── alerts.py
│   │   └── auth.py
│   │
│   ├── models/
│   │   ├── densenet_classifier.py
│   │   └── genai_summary.py
│   │
│   ├── database/
│   │   └── schema.sql
│   │
│   └── utils/
│       ├── preprocessing.py
│       └── alert_sender.py
│
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   └── pages/
│   └── service-worker.js
│
├── model/
│   ├── train.py
│   ├── evaluate.py
│   └── export_onnx.py
│
├── data/
├── notebooks/
├── docker-compose.yml
├── requirements.txt
└── README.md
```
🚀 Getting Started
📋 Prerequisites

Ensure the following are installed:

Python 3.10+
Node.js 18+
PostgreSQL 14+
Docker (Optional)
⚙️ Backend Setup
1️⃣ Clone Repository
git clone https://github.com/VaishnaviBorse07/OralVision.git

cd OralVision
2️⃣ Create Virtual Environment
cd backend

python -m venv venv
Activate Environment
Windows
venv\Scripts\activate
Linux / macOS
source venv/bin/activate
3️⃣ Install Dependencies
pip install -r requirements.txt
4️⃣ Configure Environment Variables

Create a .env file inside the backend/ directory:

DATABASE_URL=postgresql://user:password@localhost:5432/oralvision

OPENAI_API_KEY=your_openai_api_key

HOSPITAL_ALERT_WEBHOOK=your_webhook_url

SECRET_KEY=your_secret_key
5️⃣ Run Backend Server
uvicorn main:app --reload --host 0.0.0.0 --port 8000

Backend will run at:

http://localhost:8000
💻 Frontend Setup
cd frontend

npm install

npm start

Frontend will run at:

http://localhost:3000
🐳 Run with Docker
docker-compose up --build
🔌 API Endpoints
Method	Endpoint	Description
POST	/api/predict	Upload image & get risk prediction
GET	/api/summary/{case_id}	Fetch AI-generated summary
POST	/api/alert	Trigger hospital referral
GET	/api/history	Fetch patient scan history
POST	/api/auth/login	User authentication
📤 Sample API Request
/api/predict
POST /api/predict
Content-Type: multipart/form-data

{
  "image": "<uploaded_file>",
  "patient_id": "P-20240315-001"
}
📥 Sample API Response
{
  "case_id": "C-20240315-001",
  "risk_level": "High",
  "confidence": 0.91,
  "summary": "The scan shows lesion characteristics consistent with high-risk oral tissue abnormality. Immediate referral to an oncologist is recommended.",
  "referral_triggered": true
}
📊 Results
Metric	Value
Model	DenseNet121
Inference Speed	< 2 Seconds
Risk Categories	Low / Medium / High
Deployment	Mobile Optimized
🎯 Key Highlights

✅ Offline-capable Progressive Web App
✅ AI-generated clinical summaries
✅ Real-time mobile inference
✅ Rural healthcare focused
✅ Low-end Android optimization
✅ Automatic hospital referral alerts
✅ Multilingual-ready system

🏆 Recognition
Event	Achievement
SheInspires Hackathon 2026	Project Presentation
🔮 Future Enhancements
 Regional language support (Hindi, Marathi, Telugu)
 Explainable AI using Grad-CAM
 Integration with National Health Mission (NHM)
 Expanded oral lesion datasets
 Government healthcare deployment support
 APK release for healthcare tablets
👩‍💻 Team
Vaishnavi BOrse

Passionate developers focused on building impactful AI-powered healthcare solutions for underserved communities.

📜 License

This project is developed for academic, research, and healthcare innovation purposes.
