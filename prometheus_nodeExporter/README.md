# Monitorización del Sistema (Prometheus + Node Exporter + Alertmanager)

Módulo encargado de la recolección de métricas en tiempo real (CPU, RAM, disco y red), visualización y gestión de alertas de la infraestructura del proyecto.

## Estructura de archivos
* `docker-compose.yml`: Despliegue local para pruebas y desarrollo.
* `docker-stack.yml`: Despliegue en producción sobre **Docker Swarm** (`node-exporter` en modo global en todas las Raspberry Pi; `prometheus` y `alertmanager` en el nodo manager).
* `prometheus.yml`: Configuración de intervalos de lectura (*scrape*) y objetivos (*targets*).
* `alert.rules.yml`: Reglas de detección de fallos (nodo caído, CPU > 85%, RAM libre < 15%, disco libre < 10%).
* `alertmanager.yml`: Enrutamiento y envío de notificaciones hacia Discord.

## Puertos utilizados
* **9090**: Interfaz web y API de Prometheus (`/targets`, `/graph`, `/alerts`).
* **9100**: Exportador de métricas de hardware y sistema operativo (`Node Exporter`).
* **9093**: Panel de gestión de notificaciones (`Alertmanager`).

## Despliegue rápido

### En entorno local (Docker Compose)
```bash
docker compose up -d