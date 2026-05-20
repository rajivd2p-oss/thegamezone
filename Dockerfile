FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py utils.py account.py ./

CMD gunicorn -w 4 -b 0.0.0.0:${PORT:-5000} app:app
