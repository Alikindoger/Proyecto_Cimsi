FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
WORKDIR /app

RUN pip install --no-cache-dir websockets==15.0.1
COPY src/ ./

EXPOSE 8081
CMD ["python", "server.py"]