FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Dependencies in their own layer: rebuilt only when requirements.txt changes.
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app/ ./app/

# Unprivileged user; owns /app so the default SQLite file can be created when no
# DATABASE_URL is given (docker compose points it at Postgres instead).
RUN useradd --create-home --uid 10001 appuser && chown appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
