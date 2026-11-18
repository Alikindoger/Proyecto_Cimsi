extends CharacterBody2D


const SPEED = 300.0
const JUMP_VELOCITY = -400.0

var is_local = false

func _physics_process(delta: float) -> void:
	if is_local:
		var directionX := Input.get_axis("ui_left", "ui_right")
		var directionY := Input.get_axis("ui_up", "ui_down")
		if directionX || directionY:
			velocity.x = directionX * SPEED
			velocity.y = directionY * SPEED
			
		else:
			velocity.x = move_toward(velocity.x, 0, SPEED)
			velocity.y = move_toward(velocity.y, 0, SPEED)
		
		if velocity != Vector2.ZERO:
			NetworkClient.player_move(position)
		
	
	move_and_slide()
