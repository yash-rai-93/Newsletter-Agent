# ============================================================
# Newsletter Agent — Docker build for Hugging Face Spaces
# Single container: FastAPI serves both the API and the
# pre-built React frontend as static files on port 7860.
# ============================================================

# ── Stage 1: Build the React frontend ──────────────────────
FROM node:20-slim AS frontend-builder

WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install --legacy-peer-deps

COPY frontend/ .
# Point API calls to the same origin (FastAPI handles /api/*)
RUN npm run build


# ── Stage 2: Python backend ─────────────────────────────────
FROM python:3.11-slim

# HF Spaces uses port 7860
ENV PORT=7860
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source
COPY backend/ ./backend/

# Copy built frontend into FastAPI's static files directory
COPY --from=frontend-builder /app/frontend/dist ./static/

# Outputs directory
RUN mkdir -p /app/outputs

# Expose HF Spaces port
EXPOSE 7860

# Start FastAPI (main_hf.py serves static files too)
CMD ["uvicorn", "backend.main_hf:app", "--host", "0.0.0.0", "--port", "7860"]
