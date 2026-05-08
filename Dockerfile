FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py utils.py account.enc ani_libs.bin devices ./

EXPOSE 5000

CMD gunicorn -w 4 -b 0.0.0.0:${PORT:-5000} app:app
