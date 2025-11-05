from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class TrainingSessionCreate(BaseModel):
    manager_name: str
    company_description: Optional[str] = None
    difficulty_level: Optional[str] = None


class TrainingSessionUpdate(BaseModel):
    session_end: Optional[datetime] = None
    conversation_log: Optional[str] = None
    ai_analysis: Optional[str] = None
    score: Optional[float] = None
    feedback: Optional[str] = None
    status: Optional[str] = None


class CompleteSessionRequest(BaseModel):
    conversation_log: str


class TrainingSessionResponse(BaseModel):
    id: int
    manager_name: str
    session_start: datetime
    session_end: Optional[datetime]
    conversation_log: Optional[str]
    ai_analysis: Optional[str]
    score: Optional[float]
    feedback: Optional[str]
    status: str
    company_description: Optional[str] = None
    difficulty_level: Optional[str] = None
    session_system_prompt: Optional[str] = None

    class Config:
        from_attributes = True


class ConversationAnalysis(BaseModel):
    score: float
    strengths: list[str]
    areas_for_improvement: list[str]
    specific_feedback: str
    key_moments: list[str]


class TrainerSettings(BaseModel):
    company_description: Optional[str] = None
    difficulty_level: Optional[str] = None
