class_name GameManager

extends Node2D

# Escena en la que se introducen los personajes
var player_scene : PackedScene = preload("res://player.tscn")

# Contenedor donde se crean los jugadores
@onready var player_container = $Players

# Variables sobre el jugador que se crea
var my_player_id : String
var my_player_node 
var is_connected : bool = false

func _ready() -> void:
	# Comprueba la conexión con el gameManager
	if NetworkClient.gameManager != null:
		queue_free()
		push_warning("Hay dos scripts de gameManager")
	
	NetworkClient.gameManager = self

# Función que crea un jugador y lo añade al contenedor de jugadores
func add_player(id : String, is_local = false):
	my_player_node = player_scene.instantiate()
	my_player_node.name = id# el nodo del jugador con su ID
	my_player_node.is_local = is_local
	player_container.add_child(my_player_node)
