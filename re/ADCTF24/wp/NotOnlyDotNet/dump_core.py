import idaapi
import idc
import ida_bytes

start = 0x402010
size = 0x24AA

data=ida_bytes.get_bytes(start,size)

with open("core_data.bin", "wb") as f:
    f.write(data)