FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY src ./src
COPY alembic ./alembic
COPY tests ./tests
COPY alembic.ini .
COPY pyproject.toml .

RUN useradd \
    --create-home \
    --shell /bin/bash \
    appuser

RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

HEALTHCHECK \
    --interval=30s \
    --timeout=5s \
    --start-period=10s \
    --retries=3 \
    CMD curl \
        --fail \
        http://127.0.0.1:8000/health \
        || exit 1

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]