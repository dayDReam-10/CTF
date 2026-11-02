extends Area3D

signal collided_with(name)
var flag1Triggered: = false
var flag2Triggered: = false
var t: = 0.0
var cnt: = 0

const FLAG_PREFIX: = "sec2026_PART1_"
const ROUNDS: = 8
const TOKEN_BYTES: = 4
var obj

func _ready() -> void :
    obj = GameExtension.new()

func xor_enc(plain: String) -> PackedByteArray:

    var out_buf = plain.to_utf8_buffer()
    if out_buf.size() < 8:
        out_buf.resize(8)


    var result = out_buf.slice(0, 8)



    for i in range(7):
        result[i] = result[i] ^ result[i + 1]



    result[7] = result[7] ^ result[0]

    return result


func _process(delta):


    t += delta * 2.0

    if $MeshInstance3D != null and monitoring:

        $MeshInstance3D.rotation.y += delta * 1.0


        var height = sin(t) * 0.2
        $MeshInstance3D.position.y = height


        var pulse = 1.0 + sin(t * 3.0) * 0.1
        $MeshInstance3D.scale = Vector3(pulse, pulse, pulse)

        var body = get_overlapping_bodies()
        if body.size() > 0:
            if str(get_path()) == "/root/TownScene/Trigger1":
                var label = get_node("/root/TownScene/Label2")
                label.text = "flag{sec2026_PART0_example}"


            elif str(get_path()) == "/root/TownScene/Trigger2":
                var label = get_node("/root/TownScene/Label2")
                var label1 = get_node("/root/TownScene/Label")

                var flag1 = obj.Process(xor_enc(str(label1.text).substr(7)))
                label.text = "flag{" + FLAG_PREFIX + flag1 + "}  "
