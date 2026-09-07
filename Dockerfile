# ==============================================================================
# Production Dockerfile for LedgerLens Backend
# ==============================================================================
FROM python:3.12-slim as base

# Prevent Python from writing .pyc files and buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    TESSDATA_PREFIX=/app/tools/tesseract/tessdata

# Install system dependencies including Tesseract OCR & OpenCV dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    libgl1 \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN groupadd -r appgroup && useradd -r -g appgroup -u 1000 -m appuser

WORKDIR /app

# Install Python requirements
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code and default data/models
COPY --chown=appuser:appgroup . /app/

# Set up runtime directories with proper permissions
RUN mkdir -p /app/outputs/predictions /app/outputs/reports /app/models \
    && chown -R appuser:appgroup /app

USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

EXPOSE 8000

ENV ENVIRONMENT=production \
    HOST=0.0.0.0 \
    PORT=8000 \
    WORKERS=2

CMD ["python", "run.py"]
