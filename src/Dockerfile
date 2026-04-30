# BID API — FastAPI backend
FROM python:3.11-slim AS base

# Install system dependencies for Pillow, ExifTool, etc.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libimage-exiftool-perl \
    libpng-dev \
    libjpeg-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY src/requirements-api.txt /app/requirements-api.txt
RUN pip install --no-cache-dir -r requirements-api.txt

# Copy application code
COPY bid/ /app/bid/
COPY src/ /app/src/

# Data directory (mounted as volume in docker compose)
RUN mkdir -p /data/source /data/export

ENV PYTHONPATH=/app
ENV DATABASE_URL=sqlite:////data/bid.sqlite3
ENV PROJECTS_DIR=/data/projects

EXPOSE 8000

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
