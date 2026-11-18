extends Button




func _on_button_down() -> void:
	NetworkClient.connection()
	queue_free()
