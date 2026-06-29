# Decompiled with PyLingual (https://pylingual.io)
# Internal filename: main.py
# Bytecode version: 3.9.0beta5 (3425)
# Source timestamp: 1970-01-01 00:00:00 UTC (0)

import sys
secret = [631, 1205, -500, 1021, 1879, 668, -281, 1651, 1326, 593, 428, -170, 515, 1302, 452, 41, 814, 379, 382, 629, 650, 273, 1529, 630, 418, 1207, 1076, 315, 1118, 469, 398, 1803, 647, 729, 1439, 1104]
flag = input('Please enter the flag:')
flag = [ord(c) for c in flag]
if len(flag) != 36:
    print('Wrong flag length')
    sys.exit()
encoded = [0 for _ in range(36)]
for i in range(0, 36, 9):
    encoded[i] = 3 * flag[i] + 7 * flag[i + 1] - 2 * flag[i + 2] + 5 * flag[i + 3] - 6 * flag[i + 4] - 14
    encoded[i + 1] = -5 * flag[i + 1] + 9 * flag[i + 2] + 4 * flag[i + 3] - 3 * flag[i + 4] + 7 * flag[i + 5] - 18
    encoded[i + 2] = 6 * flag[i + 0] - 4 * flag[i + 1] + 2 * flag[i + 2] - 9 * flag[i + 5] + 5 * flag[i + 6] - 25
    encoded[i + 3] = 7 * flag[i + 1] + 3 * flag[i + 3] - 8 * flag[i + 4] + 6 * flag[i + 5] - 2 * flag[i + 6] + 4 * flag[i + 7] - 30
    encoded[i + 4] = 2 * flag[i + 0] + 5 * flag[i + 2] - 4 * flag[i + 4] + 7 * flag[i + 5] + 9 * flag[i + 8] - 20
    encoded[i + 5] = 8 * flag[i + 0] - 3 * flag[i + 1] + 5 * flag[i + 3] - 6 * flag[i + 7] + 2 * flag[i + 8] - 19
    encoded[i + 6] = -7 * flag[i + 1] + 4 * flag[i + 2] - 5 * flag[i + 5] + 3 * flag[i + 6] + 6 * flag[i + 8] - 22
    encoded[i + 7] = 9 * flag[i + 0] + 2 * flag[i + 2] + 6 * flag[i + 3] - 4 * flag[i + 6] + 5 * flag[i + 7] - 3 * flag[i + 8] - 27
    encoded[i + 8] = 4 * flag[i + 0] - 5 * flag[i + 4] + 7 * flag[i + 5] + 3 * flag[i + 6] + 9 * flag[i + 7] - 2 * flag[i + 8] - 33
if encoded == secret:
    print('Correct!')
else:
    print('Wrong!')