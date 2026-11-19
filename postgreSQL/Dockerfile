FROM postgres:16-alpine

# Metadatos del contenedor
LABEL maintainer="Jose - CIMSI PostgreSQL"
LABEL description="PostgreSQL 16 optimizado para Raspberry Pi 4 (ARM64) con esquemas y datos iniciales para juego multijugador"

# Variables de entorno por defecto (pueden ser sobreescritas en docker-compose / swarm)
ENV POSTGRES_DB=cimsi_game \
    POSTGRES_USER=cimsi_user \
    POSTGRES_PASSWORD=cimsi2627

# Copiar scripts de inicialización SQL
# PostgreSQL ejecuta automáticamente los archivos .sql y .sh en orden alfabético al crear el volumen
COPY ./init/ /docker-entrypoint-initdb.d/

# Comprobación de salud básica para Docker
HEALTHCHECK --interval=10s --timeout=5s --start-period=10s --retries=3 \
  CMD pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB} || exit 1
