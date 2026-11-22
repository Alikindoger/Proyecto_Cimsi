extends Node

# Valor provisional de la url del servidor hasta su despliegue
@export var server_url : String = "ws://127.0.0.1:8081"

# Parámetros iniciales necesarios para el intercambio de datos en la conexión
# Escena en la que se encuentras todo el apartado gráfico
var player_scene : PackedScene = preload("res://player.tscn")

# Objeto que guarda todo lo relacionado con la conexión usuario-servidor
var socket := WebSocketPeer.new()

# Parámetros necesarios para manejar la posición e identidad del usuario
var my_player_id : String
var my_player_node 

# Indica si el usuario está conectado
var is_connected : bool = false

# Manejador de todo lo que aparece en el juego
var gameManager : GameManager = null

# Función que se ejecuta cuando se quiere conectar con el servidor
func connection() -> void:
	print("Conectandose a " + server_url)

 	# Si la conexión no es exitosa, se detiene el proceso del juego
	var err = socket.connect_to_url(server_url)
	set_process(true)

	if err != OK:
		print("No se ha podido conectar")
		set_process(false)
	

# Variables que limitan el ratio con el que se actualiza la posición del usuario en el servidor	
const TICKS_PER_SECOND: int = 20
const TICK_TIME: float = 1.0 / TICKS_PER_SECOND

var time_accumulator: float = 0.0

# Función que se ejecuta constantemente 
func _process(delta: float) -> void:
	time_accumulator += delta
	socket.poll() # process packets
	
	var state = socket.get_ready_state()

	# Si la conexión está abierta se mantiene intercambiando paquetes con el servidor, cuando se cierra, termina el proceso del juego
	if state == WebSocketPeer.STATE_OPEN:
		if not is_connected:
			is_connected = true
			var aux = PackedByteArray()
			print("Conectado al servidor existosamente")
		
		if time_accumulator >= TICK_TIME:
			time_accumulator -= TICK_TIME
			_on_tick()

		while socket.get_available_packet_count() > 0:
			var packet = socket.get_packet()
			var text_data = packet.get_string_from_utf8()
			_handle_server_message(text_data) # parsear metodos del string a json
	
	elif state == WebSocketPeer.STATE_CLOSING:
		pass
	
	elif state == WebSocketPeer.STATE_CLOSED:
		var code = socket.get_close_code()
		var reason = socket.get_close_reason()
		print("Conexion cerrada (" + str(code) + ": " + reason + " )")
		is_connected = false
		set_process(false)

# Realiza acciones dependiendo de los protocolos que le lleguen desde el servidor
func _handle_server_message(json_string : String):
	var data = JSON.parse_string(json_string)

	if data == null:
		print("Error parseando")
		return
	match data.get("TYPE"): # type dice el tipo de json que llega
		
		"INIT": # te metes, te manda TU información
			my_player_id = str(data.get("ID"))
			print("["+ my_player_id.substr(0,3) + "]"+ "Mi ID es:" + str(data.get("ID")))
			gameManager.add_player(my_player_id,true)
			# mandar las posiciones de otros jugadores	
			# mapa estamos 
			# nuestra posicion
		"PLAYER_RESET": # Te manda información sobre un jugador que se acba de conectar
			print("["+ my_player_id.substr(0,3) + "]"+"Jugador conectado con id" + str(data.get("ID"))) 
			gameManager.add_player(str(data.get("ID")),false) # llama a la funcion para crear el personaje

			#manda informacion del resto de jugadores conectados al iniciar la conexion
		
		#cuando te metes, te informa de los demas

		"PLAYER_MOVED": # Te manda la información sobre la posición en la que se encuentran el resto de jugadores (por implementar)
			pass
			
		"DISCONNECT": # Te dice cuando un jugador se desconecta 
			print("["+ my_player_id.substr(0,3) + "] Jugador desconectado con ID: " + str(data.get("ID")))
			#busca al jugador en la escena con su ID, y lo elimina
			#player_container.find_node(str(data.get("ID"))).queue_free() 

# Se ejecuta por cada tick (lo delimitamos con la variable TICKS_PER_SECOND)
func _on_tick():
	if my_player_node != null:
		player_move(my_player_node.position)

# Crea el json que se envía al servidor cuando el jugador se mueve
func player_move(position: Vector2):
	var message : Dictionary=  {}
	message["TYPE"] = "PLAYER_MOVE"
	message["X"] = position.x
	message["Y"] = position.y
	socket.send(JSON.stringify(message).to_utf8_buffer())
