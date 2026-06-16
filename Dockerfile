# ==========================================
# 1. Builder Stage
# ==========================================
FROM python:3.11-slim as builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies to user directory
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# ==========================================
# 2. Production Stage
# ==========================================
FROM python:3.11-slim

WORKDIR /app

# Copy Python dependencies from builder
COPY --from=builder /root/.local /root/.local

# Copy application files
COPY app/ app/
COPY migrations/ migrations/
COPY alembic.ini .env.production ./

# Set the environment files to point to .env
RUN cp .env.production .env

# Set environment paths and configurations
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV APP_ENV=production

# Expose backend port
EXPOSE 8000

# Health check using standard python urllib (no extra package required)
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

# Run migrations and start uvicorn server
CMD sh -c "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"
