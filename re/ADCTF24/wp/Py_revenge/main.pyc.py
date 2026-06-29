# Decompiled with PyLingual (https://pylingual.io)
# Internal filename: 'main.py'
# Bytecode version: 3.12.0rc2 (3531)
# Source timestamp: 1970-01-01 00:00:00 UTC (0)

import base64
secret = [27, 40, 57, 63, 24, 4, 66, 4, 100, 122, 8, 27, 21, 122, 4, 15, 122, 20, 17, 98, 25, 115, 55, 82, 74, 71, 23, 20, 9, 26, 28, 105, 95, 34, 90, 46]
flag = input('Please enter the flag:')
flag = base64.b64encode(flag.encode()).decode()
flag = [ord(c) for c in flag]
key = 'ADCTF2024'
for i in range(len(flag)):
    flag[i] ^= ord(key[i % len(key)])
    flag[i] ^= i
if flag == secret:
    print('Correct!')
else:
    print('Wrong!')