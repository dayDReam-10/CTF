extends Label

func _ready() -> void :
    get_node("/root/TownScene/Trigger1").collided_with.connect(_on_collided_with)
    get_node("/root/TownScene/Trigger2").collided_with.connect(_on_collided_with)

func _on_collided_with(name):
    text = name

func _process(delta: float) -> void :
    pass
    