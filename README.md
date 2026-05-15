OralVision — Multimodal AI for Oral Cancer Detection
An AI-powered early screening system for oral cancer, designed specifically for deployment in low-resource and rural healthcare environments. OralVision enables frontline health workers to perform early oral lesion screening using AI-driven risk assessment and real-time clinical insights.

* Problem Statement:
Oral cancer contributes to nearly one-third of all cancer cases in India. While early-stage detection significantly improves survival rates, most patients are diagnosed too late due to the lack of affordable and accessible screening systems in rural areas.
OralVision bridges this healthcare gap by providing a mobile-first AI screening solution that works on low-end Android devices and assists ASHA workers and healthcare staff in identifying high-risk oral lesions without requiring specialist intervention.

* Features
Capture oral lesion images directly from a mobile device
AI-based classification into:
Low Risk
Medium Risk
High Risk
Generative AI-powered clinical summaries
Progressive Web App (PWA) support for offline usage
Automatic hospital referral alerts for high-risk cases
Designed for low-connectivity rural healthcare environments
Optimized for low-end Android devices
Multilingual-ready architecture for regional language support
                                   ┌─────────────────────────────┐
                                   │     User / Health Worker    │
                                   │      (Mobile Device)        │
                                   └─────────────┬───────────────┘
                                                 │
                                                 ▼
                              ┌──────────────────────────────────┐
                              │        React PWA Frontend        │
                              │  • Mobile-First Interface        │
                              │  • Offline Support (PWA)         │
                              │  • Camera Capture Module         │
                              └─────────────┬────────────────────┘
                                            │ REST API
                                            ▼
                              ┌──────────────────────────────────┐
                              │         FastAPI Backend          │
                              │  • Authentication                │
                              │  • API Routing                   │
                              │  • Real-Time Inference           │
                              │  • Referral Alert Handling       │
                              └─────────────┬────────────────────┘
                                            │
                    ┌───────────────────────┴────────────────────────┐
                    │                                                │
                    ▼                                                ▼
        ┌──────────────────────────┐              ┌──────────────────────────┐
        │   DenseNet121 AI Model   │              │  Generative AI Engine    │
        │  • Oral Lesion Analysis  │              │  • Clinical Summaries    │
        │  • Risk Classification   │              │  • Plain Language Output │
        │  • Low / Med / High Risk │              │  • ASHA Worker Friendly  │
        └─────────────┬────────────┘              └─────────────┬────────────┘
                      │                                         │
                      └─────────────────┬───────────────────────┘
                                        │
                                        ▼
                           ┌──────────────────────────┐
                           │      PostgreSQL DB       │
                           │  • Patient Records       │
                           │  • Scan History          │
                           │  • Risk Reports          │
                           └─────────────┬────────────┘
                                         │
                                         ▼
                           ┌──────────────────────────┐
                           │   Hospital Alert System  │
                           │  • Auto Referral Alerts  │
                           │  • Emergency Notification│
                           │  • High-Risk Escalation  │
                           └──────────────────────────┘
* AI Model Details
Component	Details
Architecture	DenseNet121 (Fine-tuned)
Task	Multi-class Image Classification
Classes	Low / Medium / High Risk
Framework	PyTorch
Input	Oral cavity clinical RGB images
Preprocessing	Resizing, normalization, augmentation
Deployment	ONNX optimization for mobile devices
* Tech Stack
Layer	Technology
Frontend	React.js, PWA
Backend	FastAPI, Python
Deep Learning	PyTorch, torchvision
Generative AI	OpenAI API / Custom LLM
Database	PostgreSQL
Deployment	Docker, Uvicorn
Image Processing	OpenCV, Pillow
* Project Structure
OralVision/
│
├── backend/
│   ├── main.py
│   ├── routes/
│   ├── models/
│   ├── database/
│   └── utils/
│
├── frontend/
│   ├── public/
│   ├── src/
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
* Getting Started
Prerequisites
Make sure the following tools are installed:
Python 3.10+
Node.js 18+
PostgreSQL 14+
Docker (Optional)
Clone the Repository
git clone https://github.com/VaishnaviBorse07/OralVision.git
cd OralVision
* Backend Setup:
cd backend
python -m venv venv
Activate Virtual Environment
Windows
venv\Scripts\activate
Linux / Mac
source venv/bin/activate
Install Dependencies
pip install -r requirements.txt
Create .env File
DATABASE_URL=postgresql://user:password@localhost:5432/oralvision
OPENAI_API_KEY=your_openai_api_key
HOSPITAL_ALERT_WEBHOOK=your_webhook_url
SECRET_KEY=your_secret_key
Run Backend Server
uvicorn main:app --reload --host 0.0.0.0 --port 8000

* Frontend Setup:
cd frontend
npm install
npm start
Application will run at:
http://localhost:3000
Run Using Docker
docker-compose up --build
  API Endpoints
Method	Endpoint	Description
POST	/api/predict	Upload image & get risk prediction
GET	/api/summary/{case_id}	Fetch AI-generated summary
POST	/api/alert	Trigger referral alert
GET	/api/history	Fetch patient history
POST	/api/auth/login	User authentication

Sample API Request
/api/predict
POST /api/predict
Content-Type: multipart/form-data

{
  "image": "<uploaded_file>",
  "patient_id": "P-20240315-001"
}
Sample API Response
{
  "case_id": "C-20240315-001",
  "risk_level": "High",
  "confidence": 0.91,
  "summary": "The scan shows lesion characteristics consistent with high-risk oral tissue abnormality. Immediate referral to an oncologist is recommended.",
  "referral_triggered": true
}
* Results
Metric	Value
Model	DenseNet121
Inference Speed	< 2 seconds
Risk Categories	Low / Medium / High
Deployment	Mobile Optimized

* Key Highlights
Offline-capable Progressive Web App
AI-generated clinical summaries
Real-time mobile inference
Hospital auto-referral system
Rural healthcare focused
Low-end Android optimization

* Recognition
Event	Achievement
SheInspires Zensar Hackathon 2026	Presented Project
* Future Enhancements
 Regional language support (Hindi, Marathi, Telugu)
 Explainable AI using Grad-CAM
 Integration with National Health Mission (NHM)
 Expanded oral lesion dataset
 Government healthcare deployment support
 
* Authors
Developed by Vaishnavi Borse
Focused on leveraging AI for accessible rural healthcare solutions.

* License
This project is intended for academic, research, and healthcare innovation purposes.
