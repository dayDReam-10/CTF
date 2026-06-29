import base64
from Crypto.Cipher import AES

key1 = b'>k3y1_f0r_z@k0<3'    # aesKey
key2 = b'z@k0f1ndth3key2w'     # xorKey

ExpectedProcessedFlagBase64 = "qpuQkUPI8knvxgK5U0UwKCrrQeOxdY8H6YKuzcD05OKatSh0UCg8+xDIxsbppDNaY3Eflx0Va8F/7wKxVrI8Qgq0vH4BUGXBDc1fSNUww5Y="

# Base64 解码
encrypted = base64.b64decode(ExpectedProcessedFlagBase64)

# Step 1: XOR 解密
xored = bytes([encrypted[i] ^ key2[i % len(key2)] for i in range(len(encrypted))])

# Step 2: AES-CBC 解密 (Key 和 IV 相同)
cipher = AES.new(key1, AES.MODE_CBC, iv=key1)
decrypted = cipher.decrypt(xored)

# Step 3: 去除 PKCS7 填充
pad_len = decrypted[-1]
flag = decrypted[:-pad_len].decode('utf-8')

print(flag)