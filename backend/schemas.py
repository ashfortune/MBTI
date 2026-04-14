from pydantic import BaseModel
from typing import List, Dict, Optional, Union

class AnalyzeRequest(BaseModel):
    my_mbti: str
    target_mbti_input: str
    situation: str
    relationship: str
    vibe: str
    context_detail: Optional[str] = ""
    target_text: str

class AnalyzeResponse(BaseModel):
    analysis_summary: str
    probabilities: Dict[str, float]
    # plot_data: Optional[Dict] = None # Plotly data can be complex to send as JSON, better to regenerate in frontend or send as simplified list
    axis_scores: Dict[str, float]
    advice: str

class OCRResponse(BaseModel):
    text: str

class ChatStartRequest(BaseModel):
    ai_first: bool
    user_mbti: str
    target_mbti: str
    relationship: str
    situation: str

class ChatStartResponse(BaseModel):
    history: List[Dict[str, str]]
    coaching_tip: str

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    history: List[ChatMessage]
    user_input: str
    user_mbti: str
    target_mbti: str
    relationship: str
    situation: str

class ChatResponse(BaseModel):
    history: List[ChatMessage]
    coaching_tip: str

class SimulateRequest(BaseModel):
    my_mbti: str
    target_mbti_input: str
    situation: str
    relationship: str
    advice_text: str

class SimulateResponse(BaseModel):
    reaction: str
