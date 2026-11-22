# ==============================================================================
# SERVICIO: tokenManager (Autenticación y gestión de sesiones)
# PUERTO EXPUESTO: 8765 (WebSockets)
# DEPENDENCIAS DE RED:
#   - Contenedor/Servicio PostgreSQL en host "postgres" puerto 5432
#   - Contenedor/Servicio Redis en host "redis" puerto 6379
# ==============================================================================

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    # Configuración conexión Redis
    REDIS_HOST=redis \
    REDIS_PORT=6379 \
    REDIS_PASSWORD=cimsi2627 \
    # Configuración conexión Postgre
    POSTGRES_HOST=postgres \
    POSTGRES_PORT=5432 \
    POSTGRES_DB=cimsi_game \
    POSTGRES_USER=cimsi_user \
    POSTGRES_PASSWORD=cimsi2627

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY server.py .

EXPOSE 8765

CMD ["python", "server.py"]
