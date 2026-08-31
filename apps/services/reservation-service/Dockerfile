FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN useradd \
    --create-home \
    --shell /bin/bash \
    appuser

COPY requiriments.txt .

RUN pip install --no-cache-dir -r requiriments.txt

COPY pyproject.toml .
COPY alembic.ini .

COPY src ./src
COPY alembic ./alembic
COPY tests ./tests

RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

CMD [ "uvicorn","src.main:app","--host","0.0.0.0","--port","8000"]
