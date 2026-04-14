---
title: CommuniKate - MBTI AI Assistant
emoji: 💬
colorFrom: indigo
colorTo: purple
sdk: docker
pinned: false
---

# 💬 CommuniKate: MBTI AI 소통 전문가

![Header](https://images.unsplash.com/photo-1516321318423-f06f85e504b3?ixlib=rb-1.2.1&auto=format&fit=crop&w=1350&q=80)

> **"상대방의 마음을 읽고, 최적의 대화를 제안합니다."**  
> CommuniKate는 정밀한 딥러닝 분석과 최신 LLM 기술을 결합하여 개인화된 MBTI 소통 전략을 제공하는 AI 어시스턴트입니다.

---

## 🚀 주요 기능

- **🎯 메시지 분석:** 상대방의 메시지 속 언어적 습관을 분석하여 가장 유력한 MBTI 성향을 도출합니다.
- **💡 맞춤형 조언:** 나의 성향과 상대방의 성향을 고려하여 갈등을 피하고 호감을 얻을 수 있는 답변 레시피를 제안합니다.
- **🎭 실전 대화 시뮬레이션:** 특정 MBTI 성향을 가진 AI와 실시간으로 대화하며 커뮤니케이션 스킬을 연습합니다.
- **🛡️ 실시간 AI 가이드:** 대화 도중 AI 코치가 상대방의 예상 반응과 최적의 말투를 실시간으로 조언합니다.

## 🛠️ 기술 스택

### **Backend (Analysis Engine)**
- **Framework:** FastAPI
- **ML Models:** 4x BERT Axis Ensembles (local), Google Gemma 4 (LLM)
- **OCR:** Google Vision AI Integration

### **Frontend (Modern Web)**
- **Framework:** Next.js (App Router)
- **Styling:** Premium Design System (Vanilla CSS / Tailwind)
- **Visuals:** Recharts for dynamic personality mapping

---

## 📂 프로젝트 구조

```text
MBTI/
├── backend/        # FastAPI 분석 엔진 및 모델 서비스
├── frontend/       # Next.js 반응형 웹 대시보드
├── Dockerfile      # Hugging Face 배포를 위한 이미지 설정
└── README.md       # 통합 가이드 문서
```

## ⚙️ 시작하기

### **로컬 환경 실행**

**1. 백엔드 설정**
```bash
cd backend
pip install -r requirements.txt
python main.py
```

**2. 프론트엔드 설정**
```bash
cd frontend
npm install
npm run dev
```

---

## 🌐 배포 정보

- **Frontend:** Vercel (Next.js Optimized)
- **Backend:** Hugging Face Spaces (Dockerized ML Env)

---
© 2026 CommuniKate Project. All rights reserved.
