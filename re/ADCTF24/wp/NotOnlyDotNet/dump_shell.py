import idaapi
import idc
import ida_bytes

start = 0x4044D0
size = 0x1BDCC80

data=ida_bytes.get_bytes(start,size)

with open("shell_data.bin", "wb") as f:
    f.write(data)