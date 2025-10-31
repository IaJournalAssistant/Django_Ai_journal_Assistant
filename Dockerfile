FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc \
        python3-dev \
        libpq-dev \
        curl \
        ffmpeg \
        wget \
        tesseract-ocr \
        tesseract-ocr-eng \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt requirements-speech.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r requirements-speech.txt

# Pre-download AI models to avoid runtime downloads
RUN python -c "import whisper; whisper.load_model('small')" || true
RUN python -c "import nltk; nltk.download('punkt'); nltk.download('brown')" || true

# Copy project
COPY . .

# Create directories for data persistence
RUN mkdir -p /app/data /app/media /app/staticfiles

# Collect static files
RUN python manage.py collectstatic --noinput --settings=a_core.settings

# Create a non-root user
RUN adduser --disabled-password --gecos '' appuser
RUN chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Run the application
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]