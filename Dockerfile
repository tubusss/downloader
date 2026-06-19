FROM python:3.11-slim

RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 7860

# gevent воркер держит долгие соединения без таймаута
CMD ["gunicorn", "app:app", "--worker-class", "gevent", "--workers", "2", "--timeout", "600", "--bind", "0.0.0.0:7860", "--keep-alive", "30"]
