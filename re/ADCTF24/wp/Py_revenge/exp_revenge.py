import base64

secret = [27, 40, 57, 63, 24, 4, 66, 4, 100, 122, 8, 27, 21, 122, 4, 15, 122, 20, 17, 98, 25, 115, 55, 82, 74, 71, 23, 20, 9, 26, 28, 105, 95, 34, 90, 46]
key = 'ADCTF2024'
decoded = []
for i, val in enumerate(secret):
    tmp = val ^ i
    tmp ^= ord(key[i % len(key)])
    decoded.append(tmp)
decoded_str = ''.join(chr(c) for c in decoded)

flag = base64.b64decode(decoded_str).decode()
print(flag)