# ==============================================================================
# Production Dockerfile for RazorLens Backend
# ==============================================================================

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

# Install Tesseract OCR + required system libraries + all supported languages
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-ara \
    tesseract-ocr-ben \
    tesseract-ocr-deu \
    tesseract-ocr-fra \
    tesseract-ocr-guj \
    tesseract-ocr-hin \
    tesseract-ocr-ita \
    tesseract-ocr-kan \
    tesseract-ocr-mal \
    tesseract-ocr-mar \
    tesseract-ocr-nld \
    tesseract-ocr-ori \
    tesseract-ocr-pan \
    tesseract-ocr-por \
    tesseract-ocr-spa \
    tesseract-ocr-tam \
    tesseract-ocr-tel \
    tesseract-ocr-tur \
    tesseract-ocr-urd \
    libgl1 \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r appgroup && \
    useradd -r -g appgroup -u 1000 -m appuser

WORKDIR /app

# Install Python dependencies
COPY requirements.txt /app/

RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY --chown=appuser:appgroup . /app/

# Create runtime directories
RUN mkdir -p \
    /app/outputs/predictions \
    /app/outputs/reports \
    && chown -R appuser:appgroup /app

USER appuser

EXPOSE 8000

# Render provides the PORT environment variable.
CMD ["sh", "-c", "uvicorn backend:app --host 0.0.0.0 --port ${PORT:-8000}"]