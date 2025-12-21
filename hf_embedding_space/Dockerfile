FROM python:3.10-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app.py .

# Expose port
EXPOSE 7860

# Set environment variable for HuggingFace Spaces
ENV GRADIO_SERVER_NAME="0.0.0.0"

# Run the application
CMD ["python", "app.py"]
