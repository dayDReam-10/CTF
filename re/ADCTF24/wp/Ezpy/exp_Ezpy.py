from z3 import *

secret = [631, 1205, -500, 1021, 1879, 668, -281, 1651, 1326, 
          593, 428, -170, 515, 1302, 452, 41, 814, 379, 
          382, 629, 650, 273, 1529, 630, 418, 1207, 1076, 
          315, 1118, 469, 398, 1803, 647, 729, 1439, 1104]

# 创建 36 个整数变量，范围设为可打印 ASCII (32-126)
flag = [Int(f'flag_{i}') for i in range(36)]

solver = Solver()

# 添加字符范围约束
for f in flag:
    solver.add(32 <= f, f <= 126)

# 添加方程
for i in range(0, 36, 9):
    solver.add(3 * flag[i] + 7 * flag[i+1] - 2 * flag[i+2] + 5 * flag[i+3] - 6 * flag[i+4] - 14 == secret[i])
    solver.add(-5 * flag[i+1] + 9 * flag[i+2] + 4 * flag[i+3] - 3 * flag[i+4] + 7 * flag[i+5] - 18 == secret[i+1])
    solver.add(6 * flag[i] - 4 * flag[i+1] + 2 * flag[i+2] - 9 * flag[i+5] + 5 * flag[i+6] - 25 == secret[i+2])
    solver.add(7 * flag[i+1] + 3 * flag[i+3] - 8 * flag[i+4] + 6 * flag[i+5] - 2 * flag[i+6] + 4 * flag[i+7] - 30 == secret[i+3])
    solver.add(2 * flag[i] + 5 * flag[i+2] - 4 * flag[i+4] + 7 * flag[i+5] + 9 * flag[i+8] - 20 == secret[i+4])
    solver.add(8 * flag[i] - 3 * flag[i+1] + 5 * flag[i+3] - 6 * flag[i+7] + 2 * flag[i+8] - 19 == secret[i+5])
    solver.add(-7 * flag[i+1] + 4 * flag[i+2] - 5 * flag[i+5] + 3 * flag[i+6] + 6 * flag[i+8] - 22 == secret[i+6])
    solver.add(9 * flag[i] + 2 * flag[i+2] + 6 * flag[i+3] - 4 * flag[i+6] + 5 * flag[i+7] - 3 * flag[i+8] - 27 == secret[i+7])
    solver.add(4 * flag[i] - 5 * flag[i+4] + 7 * flag[i+5] + 3 * flag[i+6] + 9 * flag[i+7] - 2 * flag[i+8] - 33 == secret[i+8])

# 求解
if solver.check() == sat:
    model = solver.model()
    flag_chars = [chr(model[f].as_long()) for f in flag]
    print(''.join(flag_chars))
else:
    print('No solution found')