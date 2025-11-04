from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import os
from dotenv import load_dotenv

from database import get_db, create_tables, TrainingSession
from models import (
    TrainingSessionCreate,
    TrainingSessionUpdate,
    TrainingSessionResponse,
    CompleteSessionRequest,
)
from analyzer import ConversationAnalyzer

load_dotenv()

app = FastAPI(title="Sales Training Platform", version="1.0.0")

create_tables()

app.mount("/static", StaticFiles(directory="../frontend/static"), name="static")
templates = Jinja2Templates(directory="../frontend/templates")

try:
    analyzer = ConversationAnalyzer()
    print("Conversation analyzer initialized")
except Exception as e:
    print(f"Warning: Failed to initialize analyzer: {e}")
    analyzer = None


@app.get("/", response_class=HTMLResponse)
async def main_page(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "elevenlabs_agent_id": os.getenv("ELEVENLABS_AGENT_ID")},
    )


@app.post("/api/sessions/", response_model=TrainingSessionResponse)
async def create_session(session: TrainingSessionCreate, db: Session = Depends(get_db)):
    db_session = TrainingSession(manager_name=session.manager_name)
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session


@app.get("/api/sessions/{session_id}", response_model=TrainingSessionResponse)
async def get_session(session_id: int, db: Session = Depends(get_db)):
    session = db.query(TrainingSession).filter(TrainingSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Сессия не найдена")
    return session


@app.put("/api/sessions/{session_id}/complete", response_model=TrainingSessionResponse)
async def complete_session(
    session_id: int, request: CompleteSessionRequest, db: Session = Depends(get_db)
):
    session = db.query(TrainingSession).filter(TrainingSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Сессия не найдена")

    session.session_end = datetime.now(timezone.utc)
    session.conversation_log = request.conversation_log
    session.status = "completed"

    try:
        if analyzer:
            analysis = await analyzer.analyze_conversation(request.conversation_log)
            session.ai_analysis = analyzer.format_analysis_for_display(analysis)
            session.score = analysis.score
            session.feedback = analysis.specific_feedback
            session.status = "analyzed"
        else:
            session.ai_analysis = (
                "Анализатор недоступен. Проверьте конфигурацию сервера."
            )
            session.score = 5.0
            session.feedback = "Анализ недоступен"
            session.status = "completed"
    except Exception as e:
        print(f"Ошибка анализа: {e}")
        session.ai_analysis = f"Ошибка анализа: {str(e)}"
        session.score = 5.0
        session.feedback = "Произошла ошибка при анализе"
        session.status = "completed"

    db.commit()
    db.refresh(session)
    return session


@app.get("/api/sessions/{session_id}/analysis", response_class=HTMLResponse)
async def get_analysis(
    request: Request, session_id: int, db: Session = Depends(get_db)
):
    session = db.query(TrainingSession).filter(TrainingSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Сессия не найдена")

    return templates.TemplateResponse(
        "analysis.html", {"request": request, "session": session}
    )


@app.get("/api/sessions/", response_model=list[TrainingSessionResponse])
async def list_sessions(db: Session = Depends(get_db)):
    sessions = (
        db.query(TrainingSession).order_by(TrainingSession.session_start.desc()).all()
    )
    return sessions


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", 8000))
    debug = os.getenv("DEBUG", "True").lower() == "true"

    uvicorn.run("main:app", host=host, port=port, reload=debug)
