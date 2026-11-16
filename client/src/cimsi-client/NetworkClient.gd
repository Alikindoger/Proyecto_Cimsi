extends Node

@export var server_url : String = "ws://127.0.0.1:8081"

var socket := WebSocketPeer.new()
var my_player_id : String = ""
var is_connected : bool = false


func _ready() -> void:
	print("Conectandose a " + server_url)
	var err = socket.connect_to_url(server_url)
	if err != OK:
		print("No se ha podido conectar")
		set_process(false)

	

func _process(delta: float) -> void:
	
	socket.poll() # process packets
	
	var state = socket.get_ready_state()
	
	if state == WebSocketPeer.STATE_OPEN:
		if not is_connected:
			is_connected = true
			var aux = PackedByteArray()
			print("Conectado al servidor existosamente")
		
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
		
		"INIT": print("Mi ID es:" + str(data.get("ID")))
			# mandar las posiciones de otros jugadores	
			# mapa estamos 
			# nuestra posicion
		"PLAYER_RESET": print("La posicion de " + str(data.get("ID")) + " es ")
			#manda informacion del resto de jugadores conectados al iniciar la conexion
		
		"PLAYER_MOVED": pass
			
		"HOLA_MUNDO": print(data.get("mensaje"))


func player_move(position: Vector2):
	var message = JSON.new()
	message.put("TYPE","PLAYER_MOVE")
	message.put("X",position.x)
	message.put("Y",position.y)
	socket.send(message.to_utf8_buffer())
