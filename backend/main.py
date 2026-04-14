import os
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Optional
import uvicorn
import PIL.Image
import io

from services.classifier import MBTIClassifier
from services.llm_service import LLMService
from schemas import (
    AnalyzeRequest, AnalyzeResponse, 
    OCRResponse, 
    ChatStartRequest, ChatStartResponse, 
    ChatRequest, ChatResponse,
    SimulateRequest, SimulateResponse
)

app = FastAPI(title="CommuniKate API")

# CORS 설정 (Next.js 연동을 위해 필요)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # 개발 중에는 모두 허용, 운영 시에는 프론트엔드 도메인으로 제한 권장
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"status": "ok", "message": "CommuniKate API is running"}

@app.get("/api/health")
async def health():
    return {"status": "healthy"}

# 싱글톤 패턴으로 서비스 초기화
classifier = MBTIClassifier()
llm_service = LLMService(model_name="gemma4:latest")

@app.post("/api/analyze", response_model=AnalyzeResponse)
async def analyze(request: AnalyzeRequest):
    if not request.target_text.strip():
        raise HTTPException(status_code=400, detail="메시지를 입력해주세요.")

    probs = {}
    axis_scores = {'I/E': 0, 'S/N': 0, 'T/F': 0, 'P/J': 0}
    analysis_summary = ""
    target_mbti = ""

    if request.target_mbti_input == "자동 분석 (AI)":
        if request.context_detail and request.context_detail.strip():
            reasoning_result = await llm_service.analyze_mbti_with_reasoning(request.context_detail, request.target_text)
            target_mbti = "심도 있는 분석 중"
            analysis_summary = f"### 🧠 AI 정밀 상황 분석 리포트\n{reasoning_result}"
        else:
            analysis = classifier.predict(request.target_text)
            target_mbti = analysis["mbti"]
            confidence = analysis["confidence"]
            probs = analysis["probabilities"]
            analysis_summary = f"### 🎯 메시지 분석 결과: {target_mbti}\n**신뢰도: {confidence*100:.1f}%**"
            
            # 축 점수 계산
            for mbti, p in probs.items():
                if mbti[0] == 'I': axis_scores['I/E'] += p
                if mbti[1] == 'S': axis_scores['S/N'] += p
                if mbti[2] == 'T': axis_scores['T/F'] += p
                if mbti[3] == 'P': axis_scores['P/J'] += p
    else:
        target_mbti = request.target_mbti_input
        analysis_summary = f"### 👤 지정된 MBTI: {target_mbti}\n**사용자 직접 설정**"

    # 답변 제안 생성
    advice = await llm_service.generate_response(
        request.my_mbti, target_mbti, request.situation, 
        request.relationship, request.vibe, request.target_text
    )

    # 데이터 기반 분석 근거 추가
    if request.target_mbti_input == "자동 분석 (AI)":
        axis_data = ", ".join([f"{k}: {v*100:.1f}%" for k, v in axis_scores.items()])
        reasoning_result = await llm_service.analyze_mbti_with_reasoning(
            f"상황: {request.situation}, 관계: {request.relationship}, 분위기: {request.vibe}\n[메시지 분석 데이터] {axis_data}", 
            request.target_text
        )
        analysis_summary += f"\n\n--- \n#### 🛡️ AI 전문가의 성향 분석 가이드\n{reasoning_result}"

    return AnalyzeResponse(
        analysis_summary=analysis_summary,
        probabilities=probs,
        axis_scores=axis_scores,
        advice=advice
    )

@app.post("/api/ocr", response_model=OCRResponse)
async def ocr(file: UploadFile = File(...)):
    contents = await file.read()
    image = PIL.Image.open(io.BytesIO(contents))
    text = await llm_service.extract_text_from_image(image)
    return OCRResponse(text=text)

@app.post("/api/chat/start", response_model=ChatStartResponse)
async def chat_start(request: ChatStartRequest):
    history = []
    coaching_tip = "대화를 시작했습니다. 메시지를 보내시면 AI 코칭이 시작됩니다."
    
    if request.ai_first:
        greeting = await llm_service.generate_initial_greeting(
            request.target_mbti, request.relationship, request.situation
        )
        history.append({"role": "assistant", "content": greeting})
        coaching_tip = "AI가 먼저 인사를 건넸습니다. 대화를 이어가 보세요!"
    
    return ChatStartResponse(history=history, coaching_tip=coaching_tip)

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    if not request.user_input.strip():
        return ChatResponse(history=[h.dict() for h in request.history], coaching_tip="메시지를 입력해 주세요.")
    
    import asyncio
    history_dicts = [h.dict() for h in request.history]
    
    tasks = [
        llm_service.chat_with_persona(
            history_dicts, request.user_input, request.user_mbti, 
            request.target_mbti, request.relationship, request.situation
        ),
        llm_service.get_coaching_tip(request.user_input, request.target_mbti, request.relationship)
    ]
    
    response, coaching_tip = await asyncio.gather(*tasks)
    
    new_history = history_dicts + [
        {"role": "user", "content": request.user_input},
        {"role": "assistant", "content": response}
    ]
    
    return ChatResponse(history=new_history, coaching_tip=coaching_tip)

@app.post("/api/simulate", response_model=SimulateResponse)
async def simulate(request: SimulateRequest):
    reaction = await llm_service.simulate_reaction(
        request.my_mbti, request.target_mbti_input, 
        request.situation, request.relationship, request.advice_text
    )
    return SimulateResponse(reaction=reaction)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
