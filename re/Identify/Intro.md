# Intro

## 绪论

首先需要认识`bit` `Byte` `Hex` `Binary` `WORD` `DWORD` `QWORD` 

bit: 即0和1，八个排成一排如`1 0 1 0 0 0 1 1`成为`Byte`

Byte:也被称为字节，作为基础单位参与操作

Hex:十六进制，其中由于一位十六进制数范围是0-F(0-15),也就是2^4,故一位十六进制数为半字节(half Byte)

Binary:略

WORD:字，一个字等于两字节即16位，在C里常用`uint16_t`指代

DWORD：双字，一个双字等于四个字节，即32位，在C里常用`uint32_t`指代

QWORD：四字，一个四字等于八个字节，即64位，在C里常用`uint64_t`指代



在IDA或OD里我们常看到 dq 0x1234567890ABCDEF

这里的 dq 就是 Define Quadword

意思是"往内存里写一个 8 字节（64位）的值",对应的还有：

db = Define Byte（写1字节）

dw = Define Word（写2字节）

dd = Define Dword（写4字节）


