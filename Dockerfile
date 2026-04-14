# 1. Base 이미지 설정 (Python 3.10 slim 버전 사용)
FROM python:3.10-slim

# 2. 필수 시스템 패키지 설치
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 3. 작업 디렉토리 설정
WORKDIR /app

# 4. 의존성 파일 복사 및 설치
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. 소스 코드 및 모델 공유 파일 복사
COPY backend/ .

# 6. Hugging Face Spaces 포트 설정 (기본 7860)
ENV PORT=7860
EXPOSE 7860

# 7. FastAPI 서버 실행
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]
