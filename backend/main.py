from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import logging
import time
import os
from dotenv import load_dotenv

from database import get_db, create_tables, TrainingSession
from models import (
    TrainingSessionCreate,
    TrainingSessionUpdate,
    TrainingSessionResponse,
    CompleteSessionRequest,
    TrainerSettings,
)
from analyzer import ConversationAnalyzer
from prompt_builder import build_session_system_prompt
from elevenlabs_client import ElevenLabsClient

load_dotenv()


# -----------------------------
# Logging configuration
# -----------------------------
def configure_logging() -> logging.Logger:
    """Configure application-wide logging.

    Level can be overridden with LOG_LEVEL env var (DEBUG, INFO, WARNING, ERROR).
    """
    log_level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    # Validate level
    log_level = getattr(logging, log_level_name, logging.INFO)

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    logger = logging.getLogger("app")
    logger.info("Logging initialized with level %s", logging.getLevelName(log_level))
    return logger


logger = configure_logging()

app = FastAPI(title="Sales Training Platform", version="1.0.0")

create_tables()

app.mount("/static", StaticFiles(directory="../frontend/static"), name="static")
templates = Jinja2Templates(directory="../frontend/templates")

try:
    analyzer = ConversationAnalyzer()
    logger.info("Conversation analyzer initialized")
except Exception as e:
    logger.warning("Failed to initialize analyzer: %s", e)
    analyzer = None

elevenlabs_client = ElevenLabsClient()


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Simple request logging middleware capturing latency and status code.

    Avoids logging bodies to prevent leaking sensitive or large payloads.
    """
    start = time.perf_counter()
    client = request.client.host if request.client else "-"
    path = request.url.path
    method = request.method
    query = f"?{request.url.query}" if request.url.query else ""
    content_length = request.headers.get("content-length")

    try:
        response = await call_next(request)
        duration = time.perf_counter() - start
        logger.info(
            "%s %s%s | %s | %s | %.3fs | req_bytes=%s",
            method,
            path,
            query,
            client,
            response.status_code,
            duration,
            content_length,
        )
        return response
    except Exception:
        duration = time.perf_counter() - start
        logger.exception("Unhandled error during %s %s | %s | %.3fs", method, path, client, duration)
        raise


@app.get("/", response_class=HTMLResponse)
async def main_page(request: Request):
    logger.debug("Serving main page for client=%s", request.client.host if request.client else "-")
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "elevenlabs_agent_id": os.getenv("ELEVENLABS_AGENT_ID"),
            "elevenlabs_api_key": os.getenv("ELEVENLABS_API_KEY"),
        },
    )


@app.post("/api/sessions/", response_model=TrainingSessionResponse)
async def create_session(session: TrainingSessionCreate, db: Session = Depends(get_db)):
    session_system_prompt = build_session_system_prompt(
        company_description=session.company_description,
        difficulty_level=session.difficulty_level,
        manager_name=session.manager_name,
    )

    db_session = TrainingSession(
        manager_name=session.manager_name,
        company_description=session.company_description,
        difficulty_level=session.difficulty_level,
        session_system_prompt=session_system_prompt,
    )
    
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    logger.info(
        "Created training session id=%s manager=%s difficulty=%s",
        db_session.id,
        db_session.manager_name,
        db_session.difficulty_level,
    )
    return db_session


@app.get("/api/sessions/{session_id}", response_model=TrainingSessionResponse)
async def get_session(session_id: int, db: Session = Depends(get_db)):
    session = db.query(TrainingSession).filter(TrainingSession.id == session_id).first()
    if not session:
        logger.warning("Requested session not found id=%s", session_id)
        raise HTTPException(status_code=404, detail="Сессия не найдена")
    logger.debug("Fetched session id=%s status=%s", session.id, session.status)
    return session


@app.put("/api/sessions/{session_id}/complete", response_model=TrainingSessionResponse)
async def complete_session(
    session_id: int, request: CompleteSessionRequest, db: Session = Depends(get_db)
):
    session = db.query(TrainingSession).filter(TrainingSession.id == session_id).first()
    if not session:
        logger.warning("Attempt to complete missing session id=%s", session_id)
        raise HTTPException(status_code=404, detail="Сессия не найдена")

    session.session_end = datetime.now(timezone.utc)
    session.conversation_log = request.conversation_log
    session.status = "completed"

    try:
        if analyzer:
            logger.info("Starting analysis for session id=%s", session.id)
            analysis = await analyzer.analyze_conversation(request.conversation_log)
            session.ai_analysis = analyzer.format_analysis_for_display(analysis)
            session.score = analysis.score
            session.feedback = analysis.specific_feedback
            session.status = "analyzed"
            logger.info("Completed analysis for session id=%s score=%.2f", session.id, session.score)
        else:
            session.ai_analysis = (
                "Анализатор недоступен. Проверьте конфигурацию сервера."
            )
            session.score = 5.0
            session.feedback = "Анализ недоступен"
            session.status = "completed"
    except Exception as e:
        logger.exception("Ошибка анализа для session id=%s: %s", session.id if session else session_id, e)
        session.ai_analysis = f"Ошибка анализа: {str(e)}"
        session.score = 5.0
        session.feedback = "Произошла ошибка при анализе"
        session.status = "completed"

    db.commit()
    db.refresh(session)
    logger.debug("Finalized session id=%s status=%s", session.id, session.status)
    return session


@app.get("/api/sessions/{session_id}/analysis", response_class=HTMLResponse)
async def get_analysis(
    request: Request, session_id: int, db: Session = Depends(get_db)
):
    session = db.query(TrainingSession).filter(TrainingSession.id == session_id).first()
    if not session:
        logger.warning("Requested analysis for missing session id=%s", session_id)
        raise HTTPException(status_code=404, detail="Сессия не найдена")

    logger.debug("Rendering analysis page for session id=%s", session.id)
    return templates.TemplateResponse(
        "analysis.html", {"request": request, "session": session}
    )


@app.get("/api/sessions/", response_model=list[TrainingSessionResponse])
async def list_sessions(db: Session = Depends(get_db)):
    sessions = (
        db.query(TrainingSession).order_by(TrainingSession.session_start.desc()).all()
    )
    logger.debug("Listed sessions count=%d", len(sessions))
    return sessions


@app.get("/api/sessions/{session_id}/prompt")
async def get_session_prompt(session_id: int, db: Session = Depends(get_db)):
    session = db.query(TrainingSession).filter(TrainingSession.id == session_id).first()
    if not session:
        logger.warning("Requested prompt for missing session id=%s", session_id)
        raise HTTPException(status_code=404, detail="Сессия не найдена")
    
    logger.debug("Returned session prompt for id=%s", session.id)
    return {
        "system_prompt": session.session_system_prompt,
        "session_id": session.id,
    }


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))
    debug = os.getenv("DEBUG", "false").lower() == "true"
    log_level = os.getenv("UVICORN_LOG_LEVEL", os.getenv("LOG_LEVEL", "info")).lower()

    logger.info("Starting server on %s:%s debug=%s", host, port, debug)
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=debug,
        log_level=log_level,
    )
