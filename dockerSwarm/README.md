\# Docker Swarm · Proyecto CIMSI



\## Entorno de prueba



Despliegue local de un nodo con Docker Desktop en modo de contenedores Linux.

Ejecutar los comandos desde la raíz del repositorio en PowerShell.



\## Preparar el clúster



En una instalación nueva, ejecutar `docker swarm init`. Si ya hay un Swarm

activo, comprobar el nodo con `docker node ls`. Crear la red si todavía no existe:



```powershell

docker network create --driver overlay --attachable cimsi\_net

```



Crear los dos secretos de Swarm. Para PostgreSQL, elegir una contraseña de

prueba. Para Redis, usar el valor de `requirepass` de `redis/redis.conf`.

Si los secretos ya existen, conservar los que correspondan a este entorno.



```powershell

foreach ($nombre in @('cimsi\_postgres\_local\_password', 'cimsi\_redis\_local\_password')) {

&#x20;   if (docker secret ls --filter "name=$nombre" --format '{{.Name}}' |

&#x20;       Where-Object { $\_ -eq $nombre }) { continue }



&#x20;   $clave = Read-Host "Contraseña para $nombre" -AsSecureString

&#x20;   $temporal = \[System.IO.Path]::GetTempFileName()

&#x20;   try {

&#x20;       $credencial = \[System.Net.NetworkCredential]::new('', $clave)

&#x20;       \[System.IO.File]::WriteAllText($temporal, $credencial.Password)

&#x20;       docker secret create $nombre $temporal

&#x20;       if ($LASTEXITCODE -ne 0) { throw "Error al crear $nombre" }

&#x20;   } finally {

&#x20;       Remove-Item -LiteralPath $temporal

&#x20;       Remove-Variable clave, credencial -ErrorAction SilentlyContinue

&#x20;   }

}

```



\## Construir y desplegar



```powershell

docker build -t cimsi-token-manager:local .\\tokenManager

docker build -t cimsi-game-server:local-v2 .\\gameServer



docker stack deploy -c .\\redis\\docker-stack.yml cimsi-redis-local

docker stack deploy -c .\\dockerSwarm\\postgres-local.yml cimsi-postgres-local

```



Comprobar con `docker service ls` que Redis y PostgreSQL están en `1/1`.

PostgreSQL carga los scripts SQL del equipo al inicializar su volumen por

primera vez.



```powershell

docker stack deploy --resolve-image never -c .\\dockerSwarm\\token-manager-local.yml cimsi-token-local

docker stack deploy --resolve-image never -c .\\dockerSwarm\\game-server-local.yml cimsi-game-local

```



Esperar a que el servidor de juego esté en `1/1` antes de arrancar el proxy.



```powershell

docker stack deploy -c .\\dockerSwarm\\nginx-local.yml cimsi-nginx-local

docker service ls

```



\## Verificar



\- Redis devuelve `PONG` tras autenticarse desde otro contenedor en `cimsi\_net`.

\- PostgreSQL permite consultar `public.players` desde `cimsi\_net`.

\- TokenManager registra un jugador por WebSocket y valida su token en una segunda conexión.

\- Dos conexiones consecutivas al juego a través de NGINX reciben `INIT` y cierran con código `1000`.

\- En Godot, ejecutar `main.tscn` con F6 y pulsar \*\*Connect\*\*. El cliente

&#x20; se conecta a `ws://127.0.0.1:8081` y aparece el personaje.



\## Despliegue en Raspberry Pi



La prueba se realizó en un único nodo. Queda por verificar el clúster físico,

la distribución de las imágenes compatibles con la arquitectura de las Raspberry

Pi y el almacenamiento de PostgreSQL en el SSD del nodo correspondiente.

Antes de publicar la imagen de TokenManager en un registro, retirar las

credenciales incluidas en su Dockerfile y en los valores por defecto del código.
