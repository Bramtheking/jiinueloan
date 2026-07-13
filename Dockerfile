FROM python:3.11-slim

WORKDIR /app

# Install libpq for psycopg2 (postgres driver)
RUN apt-get update && apt-get install -y libpq-dev gcc && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

COPY . .

# Render injects $PORT at runtime
CMD uvicorn app.main:app --host 0.0.0.0 --port $PORT
