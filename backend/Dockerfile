FROM python:3.11-slim

# Prevents Python from writing .pyc files and buffers logs
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# # Install system dependencies (if needed for some Python wheels)
# RUN apt-get update \
#     && apt-get install -y --no-install-recommends build-essential \
#     && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies first (leverage Docker layer cache)
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy application code
COPY backend /app/backend
COPY frontend /app/frontend

# Expose app port
EXPOSE 8000

# Default envs (can be overridden)
ENV HOST=0.0.0.0 \
    PORT=8000 \
    DEBUG=true \
    DATABASE_URL=sqlite:////app/data/sales_training.db

# Create data dir for SQLite
RUN mkdir -p /app/data

WORKDIR /app/backend

# Start the server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]


