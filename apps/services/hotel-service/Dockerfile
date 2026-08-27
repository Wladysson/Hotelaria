FROM python:3.12-slim

LABEL maintainer="Hotel Booking Platform"
LABEL description="Hotel Service - Catálogo, hotéis, quartos e disponibilidade"
LABEL version="1.0.0"

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONHASHSEED=random

WORKDIR /app

# Dependências necessárias para execução e healthcheck
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Atualiza o pip antes da instalação das dependências
RUN pip install --no-cache-dir --upgrade pip

# Copia primeiro as dependências para aproveitar cache do Docker
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copia o código da aplicação
COPY src ./src

# Copia testes
COPY tests ./tests

# Copia migrations
COPY alembic ./alembic
COPY alembic.ini .

# Configuração do projeto
COPY pyproject.toml .
COPY README.md .

# Usuário não-root
RUN useradd \
    --create-home \
    --shell /bin/bash \
    appuser

RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

# Healthcheck da API
HEALTHCHECK \
    --interval=30s \
    --timeout=5s \
    --start-period=10s \
    --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000" ]