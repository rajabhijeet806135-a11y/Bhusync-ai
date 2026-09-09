# ──────────────────────────────────────────────────────────────────────────────
# BhuSynch AI — Backend API Docker Image
# Multi-stage build: Python 3.11 + GDAL + PostGIS client tools
# Targets NIC MeghRaj sovereign cloud deployment
# ──────────────────────────────────────────────────────────────────────────────

# Stage 1: Builder — install Python deps and compile GDAL bindings
FROM python:3.11-slim-bookworm AS builder

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gdal-bin \
    libgdal-dev \
    libgeos-dev \
    libproj-dev \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set GDAL version environment variable for Python bindings
ENV CPLUS_INCLUDE_PATH=/usr/include/gdal
ENV C_INCLUDE_PATH=/usr/include/gdal

WORKDIR /build

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# Stage 2: Runtime — slim production image
FROM python:3.11-slim-bookworm AS runtime

LABEL maintainer="BhuSynch AI Team"
LABEL description="BhuSynch AI FastAPI backend with geodesy, GeoAI, and OGC endpoints"

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV TZ=Asia/Kolkata

RUN apt-get update && apt-get install -y --no-install-recommends \
    gdal-bin \
    libgdal32 \
    libgeos3.11.1 \
    libproj25 \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed Python packages from builder
COPY --from=builder /install /usr/local

# Create non-root application user
RUN groupadd --gid 1001 bhusynch && \
    useradd --uid 1001 --gid bhusynch --shell /bin/bash --create-home bhusynch

WORKDIR /app

# Copy application code
COPY --chown=bhusynch:bhusynch . .

# Create directories for uploads and temp files
RUN mkdir -p /app/uploads /app/temp /app/logs && \
    chown -R bhusynch:bhusynch /app

USER bhusynch

# Expose the FastAPI port
EXPOSE 8000

# Health check endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run FastAPI with Uvicorn — production settings
CMD ["uvicorn", "app.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "4", \
     "--loop", "uvloop", \
     "--http", "httptools", \
     "--log-level", "info", \
     "--access-log"]
