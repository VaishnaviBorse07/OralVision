import asyncio
from functools import partial
from typing import List, Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.ai.rag import answer_query_async, SUGGESTED_QUESTIONS
from app.routers.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/chat", tags=["Chatbot"])


class HistoryItem(BaseModel):
    role: str     # "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    message: str
    history: Optional[List[HistoryItem]] = []


@router.post("")
async def chat(req: ChatRequest, current_user: User = Depends(get_current_user)):
    """
    RAG + Gemini chatbot endpoint with multi-turn history support.
    Uses fully async pipeline — no thread-pool blocking for Gemini I/O.
    """
    # Convert Pydantic models to plain dicts for rag.py
    history_dicts = [{"role": h.role, "content": h.content} for h in (req.history or [])]

    # Await the async RAG pipeline directly (no run_in_executor needed for I/O-bound Gemini)
    result = await answer_query_async(req.message.strip(), 3, history_dicts)
    return {
        "answer":         result["answer"],
        "related_topics": result.get("related_topics", []),
        "sources":        result.get("sources", []),
        "method":         result.get("method", "semantic"),
    }


@router.get("/suggestions")
def get_suggestions(current_user: User = Depends(get_current_user)):
    return {"suggestions": SUGGESTED_QUESTIONS}
