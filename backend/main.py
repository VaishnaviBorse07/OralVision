from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import threading
import logging

from app.core.config import get_settings
from app.core.database import init_db
from app.routers import auth, predict, screenings, dashboard, chat
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
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


@asynccontextmanager
async def lifespan(application: FastAPI):
    # ── Startup ──────────────────────────────────────────────────────────────
    init_db()
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

# CORS
origins = [o.strip() for o in settings.cors_origins.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
