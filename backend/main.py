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
    TrainerSettings,
)
from analyzer import ConversationAnalyzer
from prompt_builder import build_final_prompt
from elevenlabs_client import ElevenLabsClient

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

elevenlabs_client = ElevenLabsClient()


@app.get("/", response_class=HTMLResponse)
async def main_page(request: Request):
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
    # Формируем итоговый промпт
    final_prompt = build_final_prompt(
        company_description=getattr(session, "company_description", None) or "",
        difficulty_level=session.difficulty_level or "",
    )
    
    # Обновляем system prompt в ElevenLabs агенте
    try:
        await elevenlabs_client.update_agent_system_prompt(final_prompt)
    except Exception as e:
        print(f"Warning: Failed to update ElevenLabs agent prompt: {e}")
        # Продолжаем создание сессии даже если обновление агента не удалось
    
    db_session = TrainingSession(
        manager_name=session.manager_name,
        company_description=getattr(session, "company_description", None),
        difficulty_level=session.difficulty_level,
        final_system_prompt=final_prompt,
    )
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


@app.get("/api/settings/", response_model=TrainerSettings)
async def get_settings():
    """
    Возвращает текущие настройки тренажера (из последней сессии или дефолтные).
    """
    return TrainerSettings(
        company_description="",
        difficulty_level="Средний",
    )


@app.get("/api/sessions/{session_id}/prompt")
async def get_session_prompt(session_id: int, db: Session = Depends(get_db)):
    """
    Возвращает итоговый system prompt для сессии.
    """
    session = db.query(TrainingSession).filter(TrainingSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Сессия не найдена")
    
    return {
        "system_prompt": session.final_system_prompt or "",
        "session_id": session.id,
    }


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("HOST")
    port = int(os.getenv("PORT"))
    debug = os.getenv("DEBUG") == "true"

    uvicorn.run("main:app", host=host, port=port, reload=debug)
