<<<<<<< HEAD
# OralVision API & Backend Infrastructure

OralVision is an AI-powered rural oral cancer early detection platform (built for ASHA workers in India), providing multi-engine risk assessment, clinical guidance, and an integrated RAG chatbot.

## Core Features (v2.0)
- **Multi-Engine AI**: 
  1. On-device local DenseNet121 (CNN) for offline image prediction.
  2. Gemini 1.5 Flash for multimodal multimodal clinical enhancements.
  3. NPCDCS clinical heuristic fallback.
- **Enterprise Star Schema**: Optimized dimensional data model (DimGeography, DimPatient, DimRiskAssessment, DimHabits) for rapid Power BI / state-level analytics.
- **RAG Chatbot**: Semantic search powered by Sentence-Transformers (all-MiniLM-L6-v2) and Gemini over a curated 36-entry oral oncology knowledge base.
- **DPDP Act Compliance**: Patient PII (e.g. mobile numbers, Aadhar) is fully masked before storage or transmission.

## Prerequisites
- Node.js (v18+)
- Python 3.10+
- PostgreSQL (or SQLite for dev fallback)
- N8N (optional, for specialist webhook alerts)

## Quick Start (Windows)
Double-click `setup.bat` to install dependencies and run both servers concurrently.

## Manual Start
### Backend
1. `cd backend`
2. `python -m venv .venv`
3. `.venv\Scripts\activate` (Windows) or `source .venv/bin/activate` (Mac/Linux)
4. `pip install -r requirements.txt`
5. Configure `.env` (Use `cp .env.example .env` if applicable, set DATABASE_URL)
6. Run `uvicorn main:app --reload`
Wait for it to say `Application startup complete`. The DB and tables will be created automatically.
Run `python -m app.seed` to populate dummy data for demo purposes.

### Frontend
1. `cd frontend`
2. `npm install`
3. `npm run dev`

The frontend will be available at http://localhost:5173 and backend at http://localhost:8000.

---

## 🚀 Production Deployment Guide

For a tech hackathon or production launch, we recommend the following free/low-cost enterprise stack:

### 1. Database: Neon (Serverless PostgreSQL)
1. Go to [Neon.tech](https://neon.tech/) and create a free account.
2. Create a new PostgreSQL project.
3. Copy the **Connection String** (it will look like `postgresql://user:password@ep-name.region.aws.neon.tech/neondb?sslmode=require`).
4. You will use this as your `DATABASE_URL` in the backend environment variables.

### 2. Backend: Render (FastAPI)
1. Push your code to a GitHub repository.
2. Go to [Render](https://render.com/) and create a **New Web Service**.
3. Connect your GitHub repo and select the `backend` folder as the Root Directory.
4. Settings:
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn main:app --host 0.0.0.0 --port 10000`
5. Add Environment Variables:
   - `DATABASE_URL`: (Paste your Neon connection string)
   - `GOOGLE_API_KEY`: (Your Gemini API key)
   - `JWT_SECRET`: (Generate a secure random string)
   - `APP_ENV`: `production`

### 3. Frontend: Vercel (React + Vite)
1. Go to [Vercel](https://vercel.com/) and create a new project.
2. Import your GitHub repository.
3. Framework Preset: **Vite**
4. Root Directory: `frontend`
5. Environment Variables:
   - `VITE_API_BASE_URL`: (The URL of your deployed Render backend, e.g., `https://oralvision-backend.onrender.com`)
6. Click **Deploy**.

> **Note on Uploads:** In production on Render, local file uploads (the `uploads/` folder) will be lost when the server restarts. For a true enterprise setup, you should update the image upload logic in `predict.py` to save images to an AWS S3 bucket or Firebase Storage instead of the local disk.
=======
# OralVision-Multimodal-AI-for-Early-Oral-Cancer-Detection-and-Automated-Triaging-in-Rural-Healthcare
>>>>>>> b03badfa8d3fdba769e030caa00b53b57dad25aa
