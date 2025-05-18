FROM python:3.11-slim

WORKDIR /app

# 필요한 패키지 설치 (최소화)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 파이썬 패키지 설치를 위한 requirements.txt 복사
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install streamlit && \
    pip cache purge

# 설치된 패키지 확인
RUN pip list | grep streamlit

# 필요한 디렉토리 생성
RUN mkdir -p /app/db_backup

# ChromaDB 데이터 복사 (먼저 복사하여 레이어 캐싱 활용)
COPY db_backup/chroma_db /app/db_backup/chroma_db

# 프로젝트 파일 복사 (.env 파일 제외)
COPY assets /app/assets
COPY src /app/src
COPY .env.example /app/.env.example
COPY run_all.sh /app/

# 실행 권한 부여
RUN chmod +x /app/run_all.sh

# 환경변수 설정
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH="/app"
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_HEADLESS=true

# 스트림릿 앱 실행
CMD ["streamlit", "run", "/app/src/app.py"]

# 포트 노출
EXPOSE 8501 