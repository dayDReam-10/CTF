# 2026年TCTF初赛

找一下字符串可以看到是 Godot 4.5

要看游戏的逻辑我们需要解密 gdc 等，但是标准 AES key 的标志字符串被去除了

找到对应版本的源代码的 `try_open_pack`，写出对应的扫描脚本，主要是扫一下 `GDPC` 这四个字符 —— 注意 ARM64 下的指令拆分问题就好：

```asm
movz w8, #0x4447
movk w8, #0x4350, lsl #16      ; 拼成 0x43504447 = "GDPC"
```

因为 ARM64 编不进 32 位立即数，所以 `strings | grep GDPC` 是搜不到的，只能按指令扫

然后找到写死的 key，直接使用发现依旧报错

那我们再追踪 `open_and_parse` 的源代码，找到其内部的 AES 实现，发现是魔改了一小部分

标准 CFB 本来是这一句：

```c
iv[n] = *output++ = iv[n] ^ *input++;
```

这里被拆成了三行，多存了一个中间值、多异或了一个块内索引：

```c
v15 = *(a5 + v7) ^ v14;      // m = KS ^ P
*(a5 + v7) = v15;            // feedback 存中间值 m，不是密文
v16 = v15 ^ v7;              // 输出再异或块内索引 n
```

让 AI 写出对应的脚本，递归的处理文件夹内部以 gdc 为结尾的文件，然后拿去给 GDRE decompile 一下就可以恢复原 gd 逻辑了

```gd
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
```

且解密town_scene.scn可以得到

```ini
[node name="Label" type="Label" parent="."]
offset_right = 360.0
offset_bottom = 63.0
label_settings = SubResource("LabelSettings_nng2a")
horizontal_alignment = 1
script = ExtResource("6")

[ext_resource type="Script" uid="uid://ba5w8n7bbcilk" path="res://token.gd" id="6"]
```

`ExtResource("6")` 对上 `id="6"`，说明 Label 挂了 token.gd

但是我们可以看到一些关键的逻辑都没有出现在 gd 脚本内部，于是我们合理怀疑是位于 `libsec2026.so` 内部

但是静态下的so是被加密的，我们需要`frida hook`获取一下就好

查找字符串 `Process`，追踪到：

```c
sub_65340(&v3, "Process", 0);        // StringName 方法名
sub_65340(&v2, "input",   0);        // StringName 参数名
sub_5FF9C(&v4, &v3, &v2);            // MethodInfo{ name="Process", args=["input"] }
sub_4E738(&v4, sub_4E198, 0);        // 注册，call_func = sub_4E198
```

`sub_4E198` 是个跳板：

```c
return ((char*)&loc_4E528
        + ((unsigned long)&loc_4E528 & 0x20)
        + (~(unsigned long)&loc_4E528 | 0xFFFFFFFFFFFFFFDF)
        + 33)(...);
```

这个式子是恒等变形设 `A = &loc_4E528`：

- `A` 的 bit5 为 1 时，`~A | ~0x20` 退化成全 1，结果等于 `A + 0x40`
- `A` 的 bit5 为 0 时，`~A | ~0x20` 就是 `~A`，结果恒等于 `0x20`

`0x4E528` 的 bit5 是 1，所以落点 `0x4E568`，而 `0x4E548` 处正好是函数序言（`SUB SP, SP, #0x70` 加 `STP X29, X30`），所以 `Process` 的真身在 `0x4E548`

最后分析算法可以得到：

```text
输入: 8 字节（xor_enc 的输出）
  ↓
ChaCha20 加密
  key   = "Th1s ls n0t a rea1 key!!@sec2026"   (32 字节)
  nonce = "012345678901"                       (12 字节)
  ↓
8 字节密文
  ↓
每字节 %02X，循环 8 次
  ↓
16 字符大写 hex
```
