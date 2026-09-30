# ---------------------------------------------------------------------------
# Dharohar Backend — multi-stage Dockerfile
#
# Build context must be the REPOSITORY ROOT (not just ./backend) so that the
# ml/ inference modules — which live outside the backend/ directory — can be
# included.  docker-compose.yml sets `context: .` (repo root) and points
# `dockerfile: backend/Dockerfile`.
#
# Stage 1 (builder): install Python dependencies into an isolated venv
# Stage 2 (runtime): copy venv + application code only — no build tools
# ---------------------------------------------------------------------------

# ---- builder ---------------------------------------------------------------
FROM python:3.11-slim AS builder

WORKDIR /build

# System-level build dependencies (needed by some compiled wheels)
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Isolated venv — easy to copy into the runtime stage
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python deps — copy requirements first for better layer caching
COPY backend/requirements.txt ./requirements.txt
RUN pip install --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# ---- runtime ---------------------------------------------------------------
FROM python:3.11-slim AS runtime

WORKDIR /app

# Runtime-only system libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
        libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Bring in the venv from the builder stage
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Non-root user for security
RUN addgroup --system dharohar && adduser --system --ingroup dharohar dharohar

# ---- Application code ------------------------------------------------------
# Copy backend source (alembic, app/, alembic.ini)
COPY backend/alembic.ini  ./alembic.ini
COPY backend/alembic/     ./alembic/
COPY backend/app/         ./app/

# Copy ml inference modules (training code is intentionally excluded)
# These are imported by the backend services at runtime.
COPY ml/enhancement/inference/ ./ml/enhancement/inference/
COPY ml/ocr/inference/         ./ml/ocr/inference/

# Make sure there's a package __init__ so Python can import ml.* as a package
RUN touch ./ml/__init__.py ./ml/enhancement/__init__.py ./ml/ocr/__init__.py

# Writable runtime directories
RUN mkdir -p /app/uploads /app/models \
 && chown -R dharohar:dharohar /app

USER dharohar

# Expose the API port
EXPOSE 8000

# Default command — overridden in docker-compose for the celery worker
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
