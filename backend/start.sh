#!/bin/bash
# Render startup script for SHL Assessment Recommender

echo "🚀 Starting SHL Assessment Recommender API..."
echo "📍 Port: ${PORT:-10000}"
echo "🌍 Environment: ${ENVIRONMENT:-production}"

# Use gunicorn with uvicorn workers for production
exec gunicorn app.main:app \
    --workers 1 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:${PORT:-10000} \
    --timeout 120 \
    --log-level info \
    --access-logfile - \
    --error-logfile -
