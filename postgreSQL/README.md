# Módulo PostgreSQL - Capa Relacional (Proyecto CIMSI)

Este módulo implementa la capa de persistencia relacional del servidor de juego para el clúster de 6 Raspberry Pi en **Docker Swarm**.

**Responsable:** José  
**Ubicación en el clúster:** Capa de Carga y Datos — **Nodo Worker 1**

---

## 1. Alcance y Arquitectura

Para la fase inicial del proyecto se implementa un modelo **minimalista y robusto centrado en la tabla `players`** (gestión de cuentas y credenciales).

### 1.1 División de Responsabilidades: PostgreSQL vs Redis
* **PostgreSQL (Worker 1 - José):** Datos persistentes maestros. Almacena las cuentas de usuario, hashes de contraseña (`bcrypt`), correos y marcas de tiempo de conexión.
* **Redis (Worker 2 - Pablo):** Datos en memoria volátiles. Gestión exclusiva de **tokens de sesión con TTL**, coordenadas en tiempo real a alta frecuencia y mensajería Pub/Sub.

### 1.2 Flujo de Autenticación
1. El cliente solicita acceso al `TokenManager` con su usuario y contraseña.
2. `TokenManager` consulta a **PostgreSQL** mediante `verify_credentials(username, password)`.
3. Si la verificación es exitosa, `TokenManager` genera el token y lo guarda en **Redis** con su tiempo de expiración.
4. El servidor de juego (`gameServer`) valida el token entrante en microsegundos contra Redis.

---

## 2. Modelo Relacional: Tabla `players`

### 2.1 Esquema SQL

```sql
CREATE TABLE IF NOT EXISTS players (
    id BIGSERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    last_login TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_players_username ON players(username);
```

* **`id`**: Clave primaria autonumérica compatible con el motor de juego en Godot y sockets.
* **`username`**: Nombre del jugador (único e indexado para búsquedas instantáneas).
* **`password_hash`**: Almacena el hash seguro generado con `bcrypt`.
* **`updated_at`**: Se actualiza de forma automática mediante un `trigger` en cada modificación.
* **`last_login`**: Se actualiza cada vez que el usuario se autentica con éxito.

---

## 3. Decisiones de Infraestructura (Worker 1)

### 3.1 Protección de la Tarjeta SD (Criterio M10)
> [!IMPORTANT]
> Las tarjetas micro-SD de las Raspberry Pi sufren degradación acelerada ante escrituras frecuentes de registros WAL (*Write-Ahead Logging*) y transacciones. Por ello, la base de datos se almacena obligatoriamente en un **disco SSD o pendrive USB externo** montado en `/mnt/ssd/postgres_data`.

### 3.2 Seguridad Perimetral
> [!CAUTION]
> Queda estrictamente prohibido exponer el puerto `5432` a la red pública (WAN) o a través de la VIP de NGINX. Toda comunicación se realiza internamente dentro de la red Overlay de Docker (`cimsi_net`).

---

## 4. Despliegue en Producción (Docker Swarm)

### Paso 1: Configurar el almacenamiento SSD en Worker 1
En la Raspberry Pi física designada como **Worker 1**:
```bash
sudo mkdir -p /mnt/ssd/postgres_data
sudo mkdir -p /mnt/ssd/backups
sudo chown -R 999:999 /mnt/ssd/postgres_data
sudo chmod 700 /mnt/ssd/postgres_data
```

### Paso 2: Asignar Label al Nodo en Docker Swarm (Ansible / Miembro 6)
Desde el nodo **Manager 1** (líder de Swarm):
```bash
docker node update --label-add db=postgres <ID_O_HOSTNAME_WORKER_1>
```

### Paso 3: Crear la Red Overlay (si no está creada)
```bash
docker network create --driver overlay --attachable cimsi_net
```

### Paso 4: Desplegar el Stack
```bash
docker stack deploy -c postgreSQL/docker-stack.yml cimsi
```

---

## 5. Integración con el Equipo (Python / Async)

En `client_example/db_helper.py` se proporciona la clase de conexión asíncrona lista para importar:

```python
from db_helper import db

await db.connect()

# 1. Registrar un nuevo jugador:
nuevo_id = await db.create_player(username="jugador1", password_raw="clave123", email="j1@correo.es")

# 2. Verificar credenciales (TokenManager):
player = await db.verify_credentials(username="jugador1", password_raw="clave123")
if player:
    print(f"Usuario válido. ID: {player['id']}")
    # -> Aquí TokenManager emite el token y lo guarda en Redis con TTL

await db.disconnect()
```

---

## 6. Pruebas Locales (Desarrollo en PC)

```bash
cd postgreSQL
docker compose up -d
./scripts/test_connection.sh
```

Ejecutar prueba en Python:
```bash
cd client_example
pip install -r requirements.txt
python example_usage.py
```
