#!/bin/bash
# Render startup script for SHL Assessment Recommender

echo "🚀 Starting SHL Assessment Recommender API..."
echo "📍 Port: ${PORT:-10000}"
echo "🌍 Environment: ${ENVIRONMENT:-production}"

# Use uvicorn directly - binds port immediately
exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port ${PORT:-10000} \
    --log-level info \
    --timeout-keep-alive 120
