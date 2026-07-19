FROM python:3.13-slim

# Set work directory
WORKDIR /app

# Install system dependencies needed for cryptography and C-extensions
# Added build-essential to ensure C-extensions in requirements compile correctly
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Set environment variables for production
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Expose port (ensure it matches your app's default)
EXPOSE 5000

# Use Gunicorn with threads to support the locking mechanism we implemented
# --threads 2 is added to handle the thread-safe mock state efficiently
CMD ["sh", "-c", "gunicorn -w 4 --threads 2 -b 0.0.0.0:${PORT:-5000} app:app"]
