FROM python:3.11.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y gcc libpq-dev && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Copy static and templates from frontend
COPY frontend/static ./static
COPY frontend/templates ./templates

EXPOSE 5000

# Create tables and start app
CMD python -c "from app import app, db; app.app_context().push(); db.create_all()" && gunicorn --bind 0.0.0.0:5000 app:app
