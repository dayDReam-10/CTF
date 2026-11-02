extends Label

const TOKEN_LEN: = 8
const CHARS: = "0123456789abcdef"


var rng: = RandomNumberGenerator.new()


func generate_token(len: int) -> String:
    var s: = ""
    for i in len:
        var idx = rng.randi_range(0, CHARS.length() - 1)
        s += CHARS[idx]
    return s

var score = 0

func _ready() -> void :

    rng.randomize()
    text = "Token: " + generate_token(TOKEN_LEN)
    print(text)
