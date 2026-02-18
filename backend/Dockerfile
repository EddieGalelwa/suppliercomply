# Use official Python 3.11 image (slim for smaller size)
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies (for psycopg2 and Pillow)
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for better caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Expose port (Railway sets PORT env var, but we expose for clarity)
EXPOSE 5000

# Run gunicorn (Railway provides PORT env var)
CMD gunicorn --bind 0.0.0.0:${PORT:-5000} app:app
