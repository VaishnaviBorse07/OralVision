from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import os
import threading
import logging

from app.core.config import get_settings
from app.core.database import init_db
from app.routers import auth, predict, screenings, dashboard, chat

settings = get_settings()
log = logging.getLogger("startup")


def _warmup():
    """Pre-warm the RAG embedder in a background thread."""
    try:
        from app.ai.rag import _load_embedder, _get_kb_embeddings
        _load_embedder()
        _get_kb_embeddings()
        log.info("RAG embedder warm-up complete")
    except Exception as e:
        log.warning("RAG warm-up skipped: %s", e)


def _seed_default_users():
    """Ensure default admin and worker users exist (idempotent)."""
    try:
        from app.core.database import SessionLocal
        from app.models.user import User, UserRole
        from app.core.security import hash_password
        db = SessionLocal()
        if not db.query(User).filter(User.email == "admin@oralvision.ai").first():
            db.add(User(
                name="Dr. Priya Sharma",
                email="admin@oralvision.ai",
                password_hash=hash_password("admin123"),
                role=UserRole.admin,
            ))
            log.info("Seeded admin user")
        if not db.query(User).filter(User.email == "worker@oralvision.ai").first():
            db.add(User(
                name="Rahul Deshmukh",
                email="worker@oralvision.ai",
                password_hash=hash_password("worker123"),
                role=UserRole.clinic_worker,
            ))
            log.info("Seeded worker user")
        db.commit()
        db.close()
    except Exception as e:
        log.warning("User seeding skipped: %s", e)


@asynccontextmanager
async def lifespan(application: FastAPI):
    # ── Startup ──────────────────────────────────────────────────────────────
    init_db()
    _seed_default_users()
    threading.Thread(target=_warmup, daemon=True).start()
    yield
    # ── Shutdown (nothing needed yet) ────────────────────────────────────────


app = FastAPI(
    title="OralVision API",
    description="AI-Powered Rural Oral Cancer Screening Platform — Gemini 1.5 Flash + Star Schema",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS — must be registered BEFORE exception handlers so headers are present on errors too
origins = [o.strip() for o in settings.cors_origins.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Custom exception handler so CORS headers are preserved on 4xx/5xx ────────
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    origin = request.headers.get("origin", "")
    headers = {}
    if origin in origins or "*" in origins:
        headers["Access-Control-Allow-Origin"] = origin
        headers["Access-Control-Allow-Credentials"] = "true"
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)},
        headers=headers,
    )


# Static file serving for uploaded images
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Routers
app.include_router(auth.router)
app.include_router(predict.router)
app.include_router(screenings.router)
app.include_router(dashboard.router)
app.include_router(chat.router)


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok", "service": "OralVision API", "version": "2.0.0"}
