extends Control

var town: Node3D = null

func _ready():

    call_deferred("_load_scene", preload("res://vehicles/car_base.tscn"))


func _load_scene(car_scene: PackedScene):

    var car: Node3D = car_scene.instantiate()
    car.name = "car"


    town = preload("res://town/town_scene.tscn").instantiate()


    town.get_node(^"InstancePos").add_child(car)


    town.get_node(^"Spedometer").car_body = car.get_child(0)


    get_parent().add_child(town)


    hide()
