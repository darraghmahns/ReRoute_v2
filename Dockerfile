# Multi-stage build for production deployment
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install

COPY frontend/ .
RUN npm run build

# Backend stage
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Copy backend dependency files and install with pip
COPY backend/pyproject.toml ./
RUN pip install fastapi uvicorn sqlalchemy alembic psycopg2-binary \
    pydantic pydantic-settings python-multipart email-validator \
    requests openai geopy numpy python-jose passlib bcrypt celery redis

# Copy backend application
COPY backend/ .

# Copy built frontend
COPY --from=frontend-builder /app/frontend/dist ./static

# Create non-root user
RUN adduser --disabled-password --gecos '' appuser \
    && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Run the application (Cloud Run uses PORT env var)
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}