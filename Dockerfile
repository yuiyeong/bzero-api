# Multi-stage build for optimized image size
FROM python:3.12-slim AS builder

WORKDIR /app

# 시스템 패키지 설치 (빌드 도구)
RUN apt-get update && apt-get install -y \
    gcc g++ curl \
    && rm -rf /var/lib/apt/lists/*

# uv 설치
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:${PATH}"

# 프로젝트 메타 파일(README 포함) 먼저 복사 후 의존성 설치
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev

# Runtime stage
FROM python:3.12-slim

WORKDIR /app

# 런타임 필수 패키지만 설치
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# builder stage에서 uv와 의존성 복사
COPY --from=builder /root/.local /root/.local
COPY --from=builder /app/.venv /app/.venv
ENV PATH="/root/.local/bin:/app/.venv/bin:${PATH}"

# 소스 복사: src 레이아웃 유지
COPY src/ ./src/

# 환경 변수
ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# 비 root 사용자 생성 (보안 강화)
RUN useradd -m -u 1000 bezero && \
    chown -R bezero:bezero /app
USER bezero

# API 포트
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# Gunicorn 설정 (환경변수로 조정 가능)
ENV GUNICORN_WORKERS=4
ENV GUNICORN_THREADS=2

# 기본 명령어 (docker-compose에서 override 가능)
# API: gunicorn bzero.main:app -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
# Worker: celery -A bzero.worker.app worker --loglevel=info
# Beat: celery -A bzero.worker.app beat --loglevel=info
CMD ["sh", "-c", "gunicorn bzero.main:app -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 --workers $GUNICORN_WORKERS --threads $GUNICORN_THREADS --worker-tmp-dir /dev/shm"]
