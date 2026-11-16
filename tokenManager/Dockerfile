FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

ENV REDIS_HOST=localhost
ENV REDIS_PORT=6379

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY server.py .

EXPOSE 8765
EXPOSE 9100

CMD ["python", "server.py"]