FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY backend/requirements.txt /app/requirements.txt

RUN apt-get update && apt-get install -y \
    build-essential \
    portaudio19-dev \
 && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -r /app/requirements.txt

COPY backend /app/backend
COPY frontend /app/frontend

EXPOSE 8000

ENV HOST=0.0.0.0 \
    PORT=8000 \
    DEBUG=false \
    DATABASE_URL=sqlite:////app/data/sales_training.db

RUN mkdir -p /app/data

WORKDIR /app/backend

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
