extends Node

@export var server_url : String = "ws://127.0.0.1:8081"

var player_scene : PackedScene = preload("res://player.tscn")

var socket := WebSocketPeer.new()
var my_player_id : String
var my_player_node 
var is_connected : bool = false

var gameManager : GameManager = null

func connection() -> void:
	print("Conectandose a " + server_url)
	var err = socket.connect_to_url(server_url)
	set_process(true)

	if err != OK:
		print("No se ha podido conectar")
		set_process(false)
	

	
const TICKS_PER_SECOND: int = 20
const TICK_TIME: float = 1.0 / TICKS_PER_SECOND

var time_accumulator: float = 0.0

func _process(delta: float) -> void:
	time_accumulator += delta
	socket.poll() # process packets
	
	var state = socket.get_ready_state()
	
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
		"PLAYER_RESET": 
			print("["+ my_player_id.substr(0,3) + "]"+"Jugador conectado con id" + str(data.get("ID"))) 
			gameManager.add_player(str(data.get("ID")),false) # llama a la funcion para crear el personaje

			#manda informacion del resto de jugadores conectados al iniciar la conexion
		
		#cuando te metes, te informa de los demas
		
		"PLAYER_MOVED": pass
			
		"DISCONNECT":
			print("["+ my_player_id.substr(0,3) + "] Jugador desconectado con ID: " + str(data.get("ID")))
			#busca al jugador en la escena con su ID, y lo elimina
			#player_container.find_node(str(data.get("ID"))).queue_free() 
			
func _on_tick():
	if my_player_node != null:
		player_move(my_player_node.position)


func player_move(position: Vector2):
	var message : Dictionary=  {}
	message["TYPE"] = "PLAYER_MOVE"
	message["X"] = position.x
	message["Y"] = position.y
	socket.send(JSON.stringify(message).to_utf8_buffer())
