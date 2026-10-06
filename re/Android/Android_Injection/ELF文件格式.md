# ELF文件格式及其加载流程

Read the f**king source code

<https://man7.org/linux/man-pages/man5/elf.5.html>

## ELF 文件格式结构

```text
偏移 0
  ┌─────────────────────┐
  │  ELF Header (Ehdr)  │  固定 64 字节（64 位）或 52 字节（32 位）
  ├─────────────────────┤
  │  Program Header     │  可选，由 e_phoff 指向，e_phnum 项
  │  Table (Phdr)       │  给内核加载器看
  ├─────────────────────┤
  │  .interp            │  动态链接器路径字符串
  ├─────────────────────┤
  │  .note.*            │  note 段
  ├─────────────────────┤
  │  .gnu.hash          │  符号哈希表
  ├─────────────────────┤
  │  .dynsym            │  动态符号表
  ├─────────────────────┤
  │  .dynstr            │  动态字符串表
  ├─────────────────────┤
  │  .gnu.version*      │  符号版本
  ├─────────────────────┤
  │  .rela.dyn          │  数据重定位表
  ├─────────────────────┤
  │  .rela.plt          │  函数重定位表
  ├─────────────────────┤
  │  .init              │  初始化代码
  ├─────────────────────┤
  │  .plt               │  过程链接表
  ├─────────────────────┤
  │  .text              │  代码
  ├─────────────────────┤
  │  .fini              │  结束代码
  ├─────────────────────┤
  │  .rodata            │  只读数据
  ├─────────────────────┤
  │  .eh_frame_hdr      │  异常处理帧索引
  ├─────────────────────┤
  │  .eh_frame          │  异常处理帧
  ├─────────────────────┤
  │  .init_array        │  构造函数数组
  ├─────────────────────┤
  │  .fini_array        │  析构函数数组
  ├─────────────────────┤
  │  .dynamic           │  动态链接信息
  ├─────────────────────┤
  │  .got               │  全局偏移表（数据部分）
  ├─────────────────────┤
  │  .got.plt           │  全局偏移表（函数部分）
  ├─────────────────────┤
  │  .data              │  已初始化全局变量
  ├─────────────────────┤
  │  .bss               │  未初始化全局变量（文件中不占空间）
  ├─────────────────────┤
  │  .comment           │  编译器版本注释
  ├─────────────────────┤
  │  .symtab            │  全部符号表
  ├─────────────────────┤
  │  .strtab            │  .symtab 的字符串
  ├─────────────────────┤
  │  .shstrtab          │  节名字符串
  ├─────────────────────┤
  │  Section Header     │  由 e_shoff 指向，e_shnum 项
  │  Table (Shdr)       │  给链接器/调试器看
  └─────────────────────┘
文件末尾
```

### ElfN_Ehdr

```c
//只看重点
#define EI_NIDENT 16

typedef struct {
    unsigned char e_ident[EI_NIDENT];  /* ELF 标识：魔数、位数、端序、ABI */
    uint16_t      e_type;              /* 文件类型：ET_REL/ET_EXEC/ET_DYN/ET_CORE */
    uint16_t      e_machine;           /* CPU 架构：EM_X86_64/EM_ARM/EM_AARCH64 */
    uint32_t      e_version;           /* 文件版本，固定 1 */
    ElfN_Addr     e_entry;             /* 程序入口点虚拟地址 */
    ElfN_Off      e_phoff;             /* 程序头表在文件中的偏移 */
    ElfN_Off      e_shoff;             /* 节头表在文件中的偏移 */
    uint32_t      e_flags;             /* 处理器特定标志 */
    uint16_t      e_ehsize;            /* ELF 头大小，固定 64 */
    uint16_t      e_phentsize;         /* 单个程序头条目大小，固定 56 */
    uint16_t      e_phnum;             /* 程序头表有几项 */
    uint16_t      e_shentsize;         /* 单个节头条目大小，固定 64 */
    uint16_t      e_shnum;             /* 节头表有几项 */
    uint16_t      e_shstrndx;          /* 节名字符串表在 SHT 里的索引 */
} ElfN_Ehdr;
```

#### e_ident[16]

```c
#define EI_MAG0        0   /* 魔数第 0 字节 */
#define EI_MAG1        1   /* 魔数第 1 字节 */
#define EI_MAG2        2   /* 魔数第 2 字节 */
#define EI_MAG3        3   /* 魔数第 3 字节 */
#define EI_CLASS       4   /* 文件类别（32/64 位） */
#define EI_DATA        5   /* 数据编码（1小端/2大端） */
#define EI_VERSION     6   /* ELF 版本 */
#define EI_OSABI       7   /* 操作系统/ABI */
#define EI_ABIVERSION  8   /* ABI 版本 */
#define EI_PAD         9   /* 填充起始位置 */
#define EI_NIDENT     16   /* e_ident 数组大小 */
```

#### e_type

```c
//指定文件类型
#define ET_NONE   0        /* 无文件类型 */
#define ET_REL    1        /* 可重定位文件 */
#define ET_EXEC   2        /* 可执行文件 */
#define ET_DYN    3        /* 共享对象文件 */
#define ET_CORE   4        /* 核心转储文件 */
#define ET_NUM    5        /* 已定义类型的数量 */
#define ET_LOOS   0xfe00   /* 操作系统特定范围起始 */
#define ET_HIOS   0xfeff   /* 操作系统特定范围结束 */
#define ET_LOPROC 0xff00   /* 处理器特定范围起始 */
#define ET_HIPROC 0xffff   /* 处理器特定范围结束 */
```

#### e_machine

```c
//标识这个 ELF 文件面向哪种 CPU 架构
#define EM_386        3   /* Intel 80386 */
#define EM_MIPS       8   /* MIPS R3000 big-endian */
#define EM_PPC64      21  /* PowerPC 64-bit */
#define EM_S390       22  /* IBM S390 */
#define EM_ARM        40  /* ARM */
#define EM_X86_64     62  /* AMD x86-64 architecture */
#define EM_AARCH64    183 /* ARM AARCH64 */
#define EM_RISCV      243 /* RISC-V */
#define EM_BPF        247 /* Linux BPF -- in-kernel virtual machine */
#define EM_LOONGARCH  258 /* LoongArch */
```

#### e_version

```c
#define EV_NONE       0   /* 无效版本 */
#define EV_CURRENT    1   /* 当前版本 */
```

#### e_entry

`e_entry` 是 `ELF Header` 里的 8 字节字段（32 位下 4 字节），存放程序入口点的虚拟地址

#### e_phoff

表示程序头表在文件中的字节偏移，链接时可选

#### e_shoff

存节头表在文件里的偏移量，运行时可选

### PHdr

可执行文件或共享对象的程序头表是一个`ELFN_Phdr`结构体数组，结构体布局如下

```c
typedef struct {
    uint32_t   p_type;    /* 段类型：PT_LOAD/PT_INTERP/PT_DYNAMIC 等 */
    uint32_t   p_flags;   /* 权限：PF_R/PF_W/PF_X */
    Elf64_Off  p_offset;  /* 段在文件中的偏移 */
    Elf64_Addr p_vaddr;   /* 段在内存中的虚拟地址 */
    Elf64_Addr p_paddr;   /* 物理地址，一般不用管 */
    uint64_t   p_filesz;  /* 段在文件中的大小 */
    uint64_t   p_memsz;   /* 段在内存中的大小 */
    uint64_t   p_align;   /* 对齐，一般 0x1000 */
} Elf64_Phdr;

typedef struct {
    uint32_t   p_type;
    Elf32_Off  p_offset;
    Elf32_Addr p_vaddr;
    Elf32_Addr p_paddr;
    uint32_t   p_filesz;
    uint32_t   p_memsz;
    uint32_t   p_flags;
    uint32_t   p_align;
} Elf32_Phdr;
```

#### p_type

```c
//段类型，4 字节。告诉内核这个段是干什么的
#define PT_NULL    0   /* 未使用 */
#define PT_LOAD    1   /* 需要加载到内存 */
#define PT_DYNAMIC 2   /* .dynamic 段，动态链接信息 */
#define PT_INTERP  3   /* 动态链接器路径 */
#define PT_NOTE    4   /* 附加注释信息 */
#define PT_SHLIB   5   /* 保留，未定义 */
#define PT_PHDR    6   /* 程序头表自身 */
#define PT_TLS     7   /* 线程局部存储 */
#define PT_GNU_EH_FRAME   0x6474e550  /* 异常处理帧 */
#define PT_GNU_STACK      0x6474e551  /* 栈权限 */
#define PT_GNU_RELRO      0x6474e552  /* 重定位后只读区域 */
#define PT_GNU_PROPERTY   0x6474e553  /* GNU 属性 */
```

#### p_flags

```c
#define PF_X  (1 << 0)   /* 可执行，值为 1 */
#define PF_W  (1 << 1)   /* 可写，值为 2 */
#define PF_R  (1 << 2)   /* 可读，值为 4 */
```

#### p_offset

段在文件中的字节偏移，8 字节，告诉内核从文件的第几字节开始读这个段

#### p_vaddr

段在内存中的虚拟地址，8 字节，告诉内核这个段映射到哪个虚拟地址

#### p_paddr

// 段在内存中的物理地址，8 字节，用于物理寻址

#### p_filesz

段在文件中的大小，8 字节，告诉内核从文件读多少字节

#### p_memsz

段在内存中的大小，8 字节。告诉内核映射多大内存
p_memsz == p_filesz：内存和文件一样大
p_memsz > p_filesz：多出来的部分是 .bss，加载时清零

#### p_align

段的对齐要求，8 字节，要求 p_vaddr 和 p_offset 对 p_align 取模相等
值 0 或 1：不需要对齐
其他：必须是 2 的幂，通常是 0x1000（4KB，页大小）

### SHdr

节头表是 `ELF` 文件里描述所有节的数组，每个元素是一个 `Elf64_Shdr` 结构体，描述一个节，布局如下

```c
typedef struct {
    uint32_t   sh_name;        /* 节名，在 .shstrtab 里的偏移 */
    uint32_t   sh_type;        /* 节类型 */
    uint64_t   sh_flags;       /* 节标志 */
    Elf64_Addr sh_addr;        /* 节在内存中的虚拟地址 */
    Elf64_Off  sh_offset;      /* 节在文件中的偏移 */
    uint64_t   sh_size;        /* 节的大小（字节） */
    uint32_t   sh_link;        /* 关联的其他节的索引 */
    uint32_t   sh_info;        /* 额外信息，解释取决于 sh_type */
    uint64_t   sh_addralign;   /* 地址对齐要求 */
    uint64_t   sh_entsize;     /* 固定大小条目的大小 */
} Elf64_Shdr;
```

#### sh_name

`sh_name` 是 4 字节字段，存节名在 `.shstrtab` 里的偏移量，不是字符串本身

#### sh_type

```c
#define SHT_PROGBITS    1   /* 程序定义的信息，代码/数据 */
#define SHT_SYMTAB      2   /* 符号表 */
#define SHT_STRTAB      3   /* 字符串表 */
#define SHT_RELA        4   /* 带显式加数的重定位 */
#define SHT_DYNAMIC     6   /* 动态链接信息 */
#define SHT_NOBITS      8   /* 文件中不占空间，如 .bss */
#define SHT_DYNSYM      11  /* 动态符号表 */
#define SHT_INIT_ARRAY  14  /* 构造函数指针数组 */
#define SHT_FINI_ARRAY  15  /* 析构函数指针数组 */
```

`sh_type` 是 4 字节字段，标识节的类型和语义

#### sh_flags

```c
#define SHF_WRITE      0x1  /* 可写 */
#define SHF_ALLOC      0x2  /* 占内存 */
#define SHF_EXECINSTR  0x4  /* 可执行 */
```

`sh_flags` 是 8 字节字段，位掩码，标识节的属性

#### sh_addr

`sh_addr` 是 8 字节字段，存节在内存中的虚拟地址，只有设了 `SHF_ALLOC` 的节才有值

#### sh_offset

`sh_offset` 是 8 字节字段，存节在文件中的字节偏移

#### sh_size

`sh_size` 是 8 字节字段，存节的大小（字节），`SHT_NOBITS` 有大小但文件里不占空间

#### sh_link

`sh_link` 是 4 字节字段，存关联的其他节的索引，含义取决于 `sh_type`

#### sh_info

`sh_info` 是 4 字节字段，存额外信息，含义取决于 `sh_type`

#### sh_addralign

`sh_addralign` 是 8 字节字段，存地址对齐要求，0 或 1 表示无约束

#### sh_entsize

`sh_entsize` 是 8 字节字段，存固定大小条目的大小，非表节为 0

举例：

```c
/* 第 1 项：.interp */
shdr[1] = {
    .sh_name      = offset_of(".interp"),   /* 去 .shstrtab 偏移处查，得 ".interp" */
    .sh_type      = SHT_PROGBITS,           /* 程序定义的内容 */
    .sh_flags     = SHF_ALLOC,              /* 占内存 */
    .sh_addr      = 0x318,                  /* 虚拟地址 0x318 */
    .sh_offset    = 0x318,                  /* 文件偏移 0x318 */
    .sh_size      = 0x1c,                   /* 大小 28 字节 */
    .sh_link      = 0,                      /* 不关联别的节 */
    .sh_info      = 0,
    .sh_addralign = 1,                      /* 字节对齐 */
    .sh_entsize   = 0,                      /* 不是表 */
};
```

### 重要Section

#### .interp

```c
/* .interp：动态链接器路径字符串 */
char interp[] = "/lib64/ld-linux-x86-64.so.2";
// 对应 Program Header 里的 PT_INTERP，内核 execve 读它，启动 ld.so
```

#### .dynsym

`.dynsym`(动态符号表)是一个 `Elf64_Sym` 数组，只在动态链接时使用，它记录本模块需要从外部导入的符号和本模块提供给外部使用的符号，布局如下

```c
typedef struct {
    uint32_t st_name;   /* 符号名，在 .dynstr 里的偏移 */
    uint8_t  st_info;   /* 类型 + 绑定 */
    uint8_t  st_other;  /* 可见性 */
    uint16_t st_shndx;  /* 所在节，UND 表示未定义 */
    uint64_t st_value;  /* 符号地址 */
    uint64_t st_size;   /* 符号大小 */
} Elf64_Sym;
```

##### st_info

```c
uint8_t st_info;

/* 一个字节装两个信息 */
/* 低 4 位 = 类型，回答"这是什么" */
/* 高 4 位 = 绑定，回答"谁有资格用它" */

/* ---------- 低 4 位：类型 ---------- */

#define STT_NOTYPE    0   /* Symbol Table Type No Type，未指定 */
#define STT_OBJECT    1   /* Symbol Table Type Object，数据对象，如全局变量 */
#define STT_FUNC      2   /* Symbol Table Type Function，函数 */
#define STT_SECTION   3   /* Symbol Table Type Section，节，重定位用 */
#define STT_FILE      4   /* Symbol Table Type File，文件名 */
#define STT_COMMON    5   /* Symbol Table Type Common，公共符号 */
#define STT_TLS       6   /* Symbol Table Type Thread Local Storage，线程局部存储 */

/* ---------- 高 4 位：绑定 ---------- */

#define STB_LOCAL     0   /* Symbol Table Bind Local，本地的，只有本文件能用 */
#define STB_GLOBAL    1   /* Symbol Table Bind Global，全局的，所有文件能用 */
#define STB_WEAK      2   /* Symbol Table Bind Weak，弱的，可以被覆盖 */

/* ---------- 拆解宏 ---------- */

#define ELF64_ST_BIND(i)   ((i) >> 4)     /* 取高 4 位，看绑定 */
#define ELF64_ST_TYPE(i)   ((i) & 0xf)    /* 取低 4 位，看类型 */
#define ELF64_ST_INFO(b,t) (((b) << 4) + ((t) & 0xf))  /* 合成一个字节 */
```

##### st_other

```c
uint8_t st_other;   /* 1 字节，最低 2 位有效 */

#define STV_DEFAULT    0   /* 默认，外部可见，可被 LD_PRELOAD 劫持 */
#define STV_INTERNAL   1   /* 处理器特定隐藏，几乎不用 */
#define STV_HIDDEN     2   /* 隐藏，外部看不到，劫持不了 */
#define STV_PROTECTED  3   /* 外部可见，但内部调用不走 PLT */

#define ELF64_ST_VISIBILITY(o)  ((o) & 0x3)   /* 取低 2 位 */
```

##### st_shndx

符号表条目里的节头索引字段，表示这个符号定义在第几个节里

##### 例子

```c
/* 导出符号：lib_add */
Elf64_Sym lib_add_sym = {
    .st_name  = offset_of("lib_add"),                  /* 名字 "lib_add"，在 .dynstr 里的偏移 */
    .st_info  = ELF64_ST_INFO(STB_GLOBAL, STT_FUNC),   /* 全局函数 */
    .st_other = STV_DEFAULT,                           /* 默认可见性，外部可见 */
    .st_shndx = 11,                                    /* 定义在 shdr[11]（.text）里 */
    .st_value = 0x1129,                                /* 相对偏移 0x1129 */
    .st_size  = 22,                                    /* 函数机器码 22 字节 */
};

/* 导入符号：printf */
Elf64_Sym printf_sym = {
    .st_name  = offset_of("printf"),                   /* 名字 "printf"，在 .dynstr 里的偏移 */
    .st_info  = ELF64_ST_INFO(STB_GLOBAL, STT_FUNC),   /* 全局函数 */
    .st_other = STV_DEFAULT,                           /* 默认可见性，外部可见 */
    .st_shndx = SHN_UNDEF,                             /* 0，未定义，从 libc 借的 */
    .st_value = 0,                                     /* 没有地址 */
    .st_size  = 0,                                     /* 没有大小 */
};
```

#### .dynstr

```c
/* .dynstr：Dynamic String Table，动态字符串表 */
char dynstr[] = "\0printf\0malloc\0lib_add\0libc.so.6\0...";
```

```c
/* 存两类东西 */

/* 1. 所有动态符号的名字，.dynsym 的 st_name 指向这里 */
Elf64_Sym dynsym[] = {
    { .st_name = 0x01 },   /* 去 .dynstr 偏移 0x01 处查，得到 "printf" */
    { .st_name = 0x08 },   /* 去 .dynstr 偏移 0x08 处查，得到 "malloc" */
    { .st_name = 0x10 },   /* 去 .dynstr 偏移 0x10 处查，得到 "lib_add" */
};

/* 2. 依赖库的名字，.dynamic 里 DT_NEEDED 的值也指向这里 */
Elf64_Dyn dyn[] = {
    { .d_tag = DT_NEEDED, .d_un.d_val = 0x18 },   /* 去 .dynstr 偏移 0x18 处查，得到 "libc.so.6" */
};
```

#### .rela.dyn

```c
/* .rela.dyn：数据重定位表，Elf64_Rela 数组 */
/* 加载时立即处理，修正 .data/.got/.init_array 里的指针 */
/* 由 DT_RELA 指向 */

typedef struct {
    Elf64_Addr r_offset;   /* 要修正的位置 */
    uint64_t   r_info;     /* 类型 + 符号索引 */
    int64_t    r_addend;   /* 加数 */
} Elf64_Rela;
```

```c
/* 假设.rela.dyn 里有一条 */
int g_count = 42;        // 全局变量，定义在 .data
int *p = &g_count;       // 全局指针，定义在 .data，初始指向 g_count

Elf64_Rela r = {
    .r_offset = 0x24dc0,        /* p 在 .data 里的地址 */
    .r_info   = R_X86_64_RELATIVE,
    .r_addend = 0x1140,         /* g_count 在 .so 内的偏移 */
};

/* ld.so 加载时 */
*(uint64_t *)(base + r.r_offset) = base + r.r_addend;
/* 把 p 的值改成 base + 0x1140 */
```

#### .rela.plt

```c
/* .rela.plt：PLT 重定位表，Elf64_Rela 数组 */
/* 延迟绑定用，第一次调用函数时才处理 */
/* 由 DT_JMPREL 指向 */

/* 比如你 call printf@plt */
/* PLT 跳到 GOT[printf] */
/* GOT[printf] 里的值由 .rela.plt 填 */
/* 填的是 libc 里 printf 的真实地址 */

typedef struct {
    Elf64_Addr r_offset;   /* .got.plt 里某个槽的地址 */
    uint64_t   r_info;     
    int64_t    r_addend;   /* 通常 0 */
} Elf64_Rela;
```

```text
r_info (8 字节)
┌───────────────────────────────┬───────────────────────────────┐
│        高 32 位               │          低 32 位              │
│        符号索引                │        重定位类型              │
│        (symbol index)         │        (relocation type)      │
└───────────────────────────────┴───────────────────────────────┘
```

作用同上

#### .init

```c
/* .init：初始化代码节，ld.so 在 main 之前调用 _init */
void _init(void);

/* 对应的 Shdr */
Elf64_Shdr shdr_init = {
    .sh_name      = offset_of(".init"),          /* 节名 */
    .sh_type      = SHT_PROGBITS,                /* 程序定义的代码 */
    .sh_flags     = SHF_ALLOC | SHF_EXECINSTR,   /* 占内存 + 可执行 */
    .sh_addr      = 0x1000,                      /* 虚拟地址 */
    .sh_offset    = 0x1000,                      /* 文件偏移 */
    .sh_size      = 0x1b,                        /* 27 字节 */
    .sh_addralign = 4,
};
```

`.init` 存 `_init` 函数的机器码，`ld.so` 在 `main` 之前调它，现代程序主要用 `.init_array`，`.init` 只做最底层初始化

#### PLT

```c
/* .plt：Procedure Linkage Table，过程链接表 */
/* 就是一段连续的机器码，每个外部函数对应一个 16 字节的 PLT 桩 */
/* 作用是跳到 .got.plt 里存的函数地址 */
/* 文件里的样子：连续排列的 16 字节机器码 */

文件偏移 0x1020:
  printf@plt:  ff 25 e2 2f 00 00    /* jmp *GOT[printf] */
               68 00 00 00 00       /* push $0，重定位索引 */
               e9 e0 ff ff ff       /* jmp PLT0 */

文件偏移 0x1030:
  malloc@plt:  ff 25 da 2f 00 00    /* jmp *GOT[malloc] */
               68 01 00 00 00       /* push $1 */
               e9 d0 ff ff ff       /* jmp PLT0 */

/* 对应的 Shdr */
Elf64_Shdr shdr_plt = {
    .sh_name      = offset_of(".plt"),           /* 节名 */
    .sh_type      = SHT_PROGBITS,                /* 代码 */
    .sh_flags     = SHF_ALLOC | SHF_EXECINSTR,   /* 占内存 + 可执行 */
    .sh_addr      = 0x1020,                      /* 虚拟地址 */
    .sh_offset    = 0x1020,                      /* 文件偏移 */
    .sh_size      = 0x170,                       /* 总大小 */
    .sh_addralign = 16,
    .sh_entsize   = 16,                          /* 每个桩 16 字节 */
};
```

这里详细解释一下，在第一次调用时`GOT`内部的值是`*printf@plt+6`，这就跳回来`push $X`指令了，这里入栈参数一个索引，该索引对应的是`rela.plt`的索引，记录该函数的一些属性

```text
call printf@plt
    ↓
printf@plt:
    jmp *GOT[printf]
    ; GOT[printf] 初始 = printf@plt + 6
    ↓
printf@plt + 6:
    push $0              ; 重定位索引 0
    jmp PLT0
    ↓
PLT0:
    push link_map
    jmp _dl_runtime_resolve
    ↓
_dl_runtime_resolve:
    1. 从栈上拿到索引 0 和 link_map
    2. 查 .rela.plt[0]
    3. 从 r_info 里拆出符号索引，找到 "printf"
    4. 在 libc 里解析出 printf 真实地址
    5. 把真实地址写到 r_offset 指向的 GOT[printf]
    6. 跳转到真正的 printf
```

#### .text

```c
/* `.text`：代码段 */
/* 所有普通函数的机器码都在这里 */
/* `sh_type = SHT_PROGBITS` */
/* `sh_flags = SHF_ALLOC | SHF_EXECINSTR` */
/* 权限 `R-X` 不可写 */
/* 逆向主战场：反汇编 函数识别 栈帧分析 调用约定 */
/* 和 `.plt` 的区别：`.plt` 是跳板代码 `.text` 是主代码 */
/* `e_entry` 通常指向 `.text` 里的 `_start` */
/* 但 `PIE` 下要加 `base` 才是真实地址 */
```

#### .rodata

```c
/* `.rodata`：只读数据 */
/* 字符串常量 跳转表 浮点常量 查找表 */
/* `sh_type = SHT_PROGBITS` */
/* `sh_flags = SHF_ALLOC` */
/* 权限 `R--` 不可写不可执行 */
/* `strings` 的来源 交叉引用字符串能快速定位逻辑 */
/* `switch` 编译成跳转表时 表通常在这里 */
/* 有些壳会把加密数据藏这里 运行时再解密 */
```

#### .init_array

```c
/* `.init_array`：构造函数数组 */
/* 本质是一个函数指针数组 每个元素 8 字节 指向一个函数 */
/* 在 `main` 之前由 `ld.so` 逐个调用 */

/* 对应的 `Shdr` */
Elf64_Shdr shdr_init_array = {
    .sh_name      = offset_of(".init_array"),           /* 节名 */
    .sh_type      = SHT_INIT_ARRAY,                     /* 构造函数指针数组 */
    .sh_flags     = SHF_ALLOC | SHF_WRITE,              /* 占内存 + 可写 */
    .sh_addr      = 0x3d80,                             /* 虚拟地址 */
    .sh_offset    = 0x3d80,                             /* 文件偏移 */
    .sh_size      = 0x10,                               /* 大小 16 字节 = 2 个函数指针 */
    .sh_link      = 0,
    .sh_info      = 0,
    .sh_addralign = 8,                                  /* 8 字节对齐 */
    .sh_entsize   = 0,                                  /* 非表节 不是固定条目 */
};

/* 文件里的样子：连续排列的 8 字节函数指针 */
文件偏移 0x3d80:
    .init_array[0]:  0x0000000000001149    /* 指向 frame_dummy */
    .init_array[1]:  0x00000000000011a3    /* 指向 my_constructor */


/* 谁来调用 */
/* 内核加载 ELF 后 把控制权交给 `ld.so` */
/* `ld.so` 完成重定位 加载依赖库 之后 */
/* 遍历 `.init_array` 从 `[0]` 到 `[N-1]` */
/* 逐个调用每个函数指针 全部返回后 才跳到 `e_entry` */

/* 程序执行顺序 */
/* `ld.so` 初始化 -> `ld.so` 加载依赖库 -> `ld.so` 重定位依赖库 */
/* -> `ld.so` 调依赖库 `.init_array` -> `ld.so` 跳主程序 `e_entry` 即 `_start` */
/* -> `_start` 调 `__libc_start_main` -> `__libc_start_main` 调主程序 `.init_array` */
```

#### .fini_array

```c
/* 在 `main` 返回之后由 `__libc_start_main` 或 `exit` 调用 */

/* 对应的 `Shdr` */
Elf64_Shdr shdr_fini_array = {
    .sh_name      = offset_of(".fini_array"),           /* 节名 */
    .sh_type      = SHT_FINI_ARRAY,                     /* 析构函数指针数组 */
    .sh_flags     = SHF_ALLOC | SHF_WRITE,              /* 占内存 + 可写 */
    .sh_addr      = 0x3d90,                             /* 虚拟地址 */
    .sh_offset    = 0x3d90,                             /* 文件偏移 */
    .sh_size      = 0x10,                               /* 大小 16 字节 = 2 个函数指针 */
    .sh_link      = 0,
    .sh_info      = 0,
    .sh_addralign = 8,                                  /* 8 字节对齐 */
    .sh_entsize   = 0,                                  /* 非表节 不是固定条目 */
};

/* 文件里的样子：连续排列的 8 字节函数指针 */
文件偏移 0x3d90:
    .fini_array[0]:  0x00000000000011b7    /* 指向 my_destructor */
    .fini_array[1]:  0x0000000000001140    /* 指向 __do_global_dtors_aux */

/* 谁来调用 */
/* `main` 返回后 控制权回到 `__libc_start_main` */
/* `__libc_start_main` 调 `exit` */
/* `exit` 先跑 `atexit` 注册的函数 */
/* 再遍历 `.fini_array` 从 `[N-1]` 到 `[0]` */
/* 注意是倒序 和 `.init_array` 相反 */
/* 全部执行完 才真正退出进程 */

/* 程序退出顺序 */
/* `main` 返回 -> `exit` -> `atexit` 回调 -> `.fini_array[N-1]` -> ... -> `.fini_array[0]` -> `_exit` 系统调用 */

```

`.fini_array` 是一个函数指针数组 `main` 返回后倒序调用 和 `.init_array` 对称

#### .dynamic

```c
/* `.dynamic` 是一个 `Elf64_Dyn` 数组 */
/* 存在文件里 加载后映射到内存 通常可写 */
/* 由 `Program Header` 里的 `PT_DYNAMIC` 指向 */
/* 内核加载 ELF 时 看到 `PT_DYNAMIC` 就知道 `.dynamic` 在哪 */
/* 然后把控制权交给 `ld.so` */
/* `ld.so` 第一步就是读 `.dynamic` */
/* 它是动态链接的总索引 其他动态相关节全靠它里面的 `DT_*` 指出来 */
/* 没有它 `ld.so` 就不知道去哪找 `.dynsym` `.dynstr` `.rela.plt` 等 */
/* 每个条目 16 字节 */
typedef struct {
    int64_t  d_tag;          /* 标签 8 字节 决定 `d_un` 怎么解释 */
    union {
        uint64_t d_val;      /* 整数值 常是偏移或大小 */
        uint64_t d_ptr;      /* 虚拟地址 */
    } d_un;                  /* 8 字节 */
} Elf64_Dyn;

/* 32 位下 每个条目 8 字节 */
typedef struct {
    int32_t  d_tag;          /* 4 字节 */
    union {
        uint32_t d_val;      /* 4 字节 */
        uint32_t d_ptr;      /* 4 字节 */
    } d_un;
} Elf32_Dyn;
/* `d_tag` 决定这条条目是什么意思 */
/* `d_un` 是联合体 同一个 8 字节 */
/* 有时当整数用 `d_val` 有时当地址用 `d_ptr` */
/* 具体用哪个 由 `d_tag` 决定 */

/* 例如 `DT_NEEDED` 的 `d_un.d_val` 是 `.dynstr` 偏移 */
/* 例如 `DT_STRTAB` 的 `d_un.d_ptr` 是 `.dynstr` 虚拟地址 */
/* 例如 `DT_STRSZ` 的 `d_un.d_val` 是 `.dynstr` 字节大小 */
//举例
文件偏移 0x3db0:
    .dynamic[0]:  DT_NEEDED      0x000000000000001b   /* 依赖库名在 `.dynstr` 偏移 0x1b */
    .dynamic[1]:  DT_NEEDED      0x0000000000000025   /* 依赖库名在 `.dynstr` 偏移 0x25 */
    .dynamic[2]:  DT_INIT        0x0000000000001000   /* `_init` 地址 */
    .dynamic[3]:  DT_FINI        0x0000000000001150   /* `_fini` 地址 */
    .dynamic[4]:  DT_INIT_ARRAY  0x0000000000003d80   /* `.init_array` 地址 */
    .dynamic[5]:  DT_INIT_ARRAYSZ 0x0000000000000010  /* `.init_array` 大小 */
    .dynamic[6]:  DT_FINI_ARRAY  0x0000000000003d90   /* `.fini_array` 地址 */
    .dynamic[7]:  DT_FINI_ARRAYSZ 0x0000000000000010  /* `.fini_array` 大小 */
    .dynamic[8]:  DT_GNU_HASH    0x00000000000002e8   /* `.gnu.hash` 地址 */
    .dynamic[9]:  DT_STRTAB      0x00000000000003c0   /* `.dynstr` 地址 */
    .dynamic[10]: DT_SYMTAB      0x0000000000000318   /* `.dynsym` 地址 */
    .dynamic[11]: DT_STRSZ       0x00000000000000f5   /* `.dynstr` 大小 */
    .dynamic[12]: DT_SYMENT      0x0000000000000018   /* `Elf64_Sym` 大小 24 */
    .dynamic[13]: DT_PLTGOT      0x0000000000004000   /* `.got.plt` 地址 */
    .dynamic[14]: DT_PLTRELSZ    0x0000000000000030   /* `.rela.plt` 大小 */
    .dynamic[15]: DT_PLTREL      0x0000000000000007   /* 重定位类型 7 = `DT_RELA` */
    .dynamic[16]: DT_JMPREL      0x00000000000005a0   /* `.rela.plt` 地址 */
    .dynamic[17]: DT_RELA        0x00000000000004a0   /* `.rela.dyn` 地址 */
    .dynamic[18]: DT_RELASZ      0x0000000000000100   /* `.rela.dyn` 大小 */
    .dynamic[19]: DT_RELAENT     0x0000000000000018   /* `Elf64_Rela` 大小 24 */
    .dynamic[20]: DT_RELACOUNT   0x0000000000000005   /* `R_X86_64_RELATIVE` 数量 */
    .dynamic[21]: DT_FLAGS_1     0x0000000008000001   /* `NOW` + `PIE` */
    .dynamic[22]: DT_NULL        0x0000000000000000   /* 数组结束标记 */
/* `ld.so` 启动流程 读 `.dynamic` 相关部分 */

/* 1. 找 `PT_DYNAMIC` 拿到 `.dynamic` 地址 */
/* 2. 遍历 `.dynamic` 遇到 `DT_NULL` 停 */
/* 3. 读 `DT_NEEDED` 加载依赖库 */
/* 4. 读 `DT_STRTAB` `DT_SYMTAB` `DT_GNU_HASH` 准备符号解析 */
/* 5. 读 `DT_RELA` `DT_RELASZ` 处理 `.rela.dyn` 数据重定位 */
/* 6. 读 `DT_JMPREL` `DT_PLTRELSZ` `DT_PLTREL` 准备 `.rela.plt` */
/* 7. 读 `DT_PLTGOT` 找到 `.got.plt` 初始化前 3 项 */
/* 8. 读 `DT_INIT_ARRAY` `DT_INIT_ARRAYSZ` 准备调构造函数 */
/* 9. 读 `DT_FLAGS_1` 看是否 `BIND_NOW` 决定立即绑定还是延迟绑定 */
/* 10. 全部处理完 跳到 `e_entry` */

/* 所以 `.dynamic` 是 `ld.so` 的导航图 */
/* 没有它 `ld.so` 完全不知道从哪下手 */
```

#### .got

```c
/* `.got`：Global Offset Table 全局偏移表 数据部分 */
/* 本质是一个指针数组 每个元素 8 字节 指向一个全局变量或数据对象 */
/* 和 `.got.plt` 分工不同：`.got` 给数据用 `.got.plt` 给函数用 */
/* 由 `.rela.dyn` 里的 `R_X86_64_GLOB_DAT` 等重定位填充 */

/* 对应的 `Shdr` */
Elf64_Shdr shdr_got = {
    .sh_name      = offset_of(".got"),                  /* 节名 */
    .sh_type      = SHT_PROGBITS,                       /* 程序定义的内容 */
    .sh_flags     = SHF_ALLOC | SHF_WRITE,              /* 占内存 + 可写 */
    .sh_addr      = 0x3fe0,                             /* 虚拟地址 */
    .sh_offset    = 0x2fe0,                             /* 文件偏移 */
    .sh_size      = 0x20,                               /* 大小 32 字节 = 4 个指针 */
    .sh_link      = 0,
    .sh_info      = 0,
    .sh_addralign = 8,                                  /* 8 字节对齐 */
    .sh_entsize   = 8,                                  /* 每个条目 8 字节 */
};

/* 文件里的样子：连续排列的 8 字节地址 */
文件偏移 0x2fe0:
    .got[0]:  0x0000000000003d80    /* 指向全局变量 g_config */
    .got[1]:  0x0000000000003d88    /* 指向全局变量 g_state */
    .got[2]:  0x0000000000000000    /* 未使用或保留 */
    .got[3]:  0x0000000000000000
```

```c
/* 为什么需要它 */
/* 位置无关代码 `PIC` 里 不能直接写全局变量的绝对地址 */
/* 因为共享库加载到哪个地址 链接时不知道 */
/* 所以代码里不写绝对地址 改成从 `.got` 里读 */
/* `.got` 里存的是真正的地址 由 `ld.so` 加载时填好 */

/* 举个例子 */
/* C 代码 `extern int g_count; int x = g_count;` */
/* 编译成 PIC 后不是直接读 `g_count` 的绝对地址 */
/* 而是先读 `.got` 里 `g_count` 的槽 拿到真实地址 再读 */
/* 代码里只有 `.got` 槽的偏移 这个偏移是固定的 */

/* 运行时怎么用 */
/* 1. 链接时 `.got` 里先填一个占位值 */
/* 2. 加载时 `ld.so` 读 `.rela.dyn` */
/* 3. 遇到 `R_X86_64_GLOB_DAT` 类型 */
/* 4. 解析符号 `g_count` 的真实地址 */
/* 5. 写到 `.rela.dyn` 条目的 `r_offset` 指向的 `.got` 槽 */
/* 6. 程序读 `.got` 槽 拿到真实地址 */
```

#### .got.plt

```c
/* `.got.plt`：Global Offset Table for PLT 全局偏移表 函数部分 */

/* 和 `.got` 分工不同：`.got` 给数据用 `.got.plt` 给函数用 */
/* 由 `.rela.plt` 里的 `R_X86_64_JUMP_SLOT` 填充 延迟绑定 */

/* 对应的 `Shdr` */
Elf64_Shdr shdr_got_plt = {
    .sh_name      = offset_of(".got.plt"),              /* 节名 */
    .sh_type      = SHT_PROGBITS,                       /* 程序定义的内容 */
    .sh_flags     = SHF_ALLOC | SHF_WRITE,              /* 占内存 + 可写 */
    .sh_addr      = 0x4000,                             /* 虚拟地址 */
    .sh_offset    = 0x3000,                             /* 文件偏移 */
    .sh_size      = 0x48,                               /* 大小 72 字节 = 9 个指针 */
    .sh_link      = 0,
    .sh_info      = 0,
    .sh_addralign = 8,                                  /* 8 字节对齐 */
    .sh_entsize   = 8,                                  /* 每个条目 8 字节 */
};

/* 文件里的样子：连续排列的 8 字节地址 */
/* 前 3 项特殊 从 [3] 开始每个对应一个 PLT 桩 */
文件偏移 0x3000:
    .got.plt[0]:  0x0000000000003db0    /* `.dynamic` 地址 */
    .got.plt[1]:  0x0000000000000000    /* `link_map` 加载时 ld.so 填 */
    .got.plt[2]:  0x0000000000000000    /* `_dl_runtime_resolve` 加载时 ld.so 填 */
    .got.plt[3]:  0x0000000000001036    /* printf 的槽 初始指向 printf@plt+6 */
    .got.plt[4]:  0x0000000000001046    /* malloc 的槽 初始指向 malloc@plt+6 */
    .got.plt[5]:  0x0000000000001056    /* free 的槽 初始指向 free@plt+6 */
    .got.plt[6]:  0x0000000000001066    /* puts 的槽 初始指向 puts@plt+6 */
    .got.plt[7]:  0x0000000000001076    /* exit 的槽 初始指向 exit@plt+6 */
    .got.plt[8]:  0x0000000000000000    /* 保留或对齐 */
```

```c

/* 前 3 项特殊 */
GOT[0] = .dynamic 地址        /* 链接时 ld 填 */
GOT[1] = link_map             /* 加载时 ld.so 填 指向当前模块的 link_map */
GOT[2] = _dl_runtime_resolve  /* 加载时 ld.so 填 指向动态链接器解析函数 */
/* 从 GOT[3] 开始 每项对应一个外部函数 也对应一个 PLT 桩 */
```

```c
/* 运行时怎么用 完整流程 */

/* ===== 链接时 ld ===== */
/* 1. 给每个外部函数分配 `.got.plt` 槽 */
/*    比如 printf -> GOT[3] malloc -> GOT[4] */
/* 2. 生成 PLT 桩 */
/*    printf@plt: jmp *GOT[3]; push $0; jmp PLT0 */
/* 3. 往 `.rela.plt` 加条目 */
/*    r_offset = &GOT[3] r_info = R_INFO(printf_sym, JUMP_SLOT) */
/* 4. `.got.plt[3]` 初始值 = printf@plt + 6 */
/*    即指向 printf@plt 里的 `push $0` 指令 */
/* 5. `.got.plt[0]` 填 `.dynamic` 地址 */
/* 6. `.got.plt[1]` `.got.plt[2]` 填 0 等 ld.so 填 */

/* ===== 加载时 ld.so ===== */
/* 1. 填 `.got.plt[1]` = link_map */
/* 2. 填 `.got.plt[2]` = _dl_runtime_resolve */
/* 3. 默认延迟绑定 不解析 `.rela.plt` */
/*    如果 `BIND_NOW` 就遍历 `.rela.plt` 全部解析填真实地址 */

```

```c
/* 和 `.got` 的区别 */
/* 项目         `.got`              `.got.plt` */
/* 用途         数据引用             函数引用 */
/* 重定位表     `.rela.dyn`         `.rela.plt` */
/* 重定位类型   `R_X86_64_GLOB_DAT` `R_X86_64_JUMP_SLOT` */
/* 填充时机     加载时立即          默认延迟到第一次调用 */
/* 前 3 项      无特殊含义          特殊 `.dynamic` link_map resolve */
/* 可写性       Partial RELRO 只读  Partial RELRO 可写 */
/*              Full RELRO 只读     Full RELRO 只读 */

/* `Partial RELRO` 下 `.got.plt` 可写 */
/* 这是 GOT 劫持的基础 */
/* 把某个函数的 GOT 槽改成 system */
/* 下次调用就跳到 system */
```

#### .data

```c
/* `.data`：已初始化全局变量 */
/* 本质是一段可读写数据 放有初值的全局变量和静态变量 */
/* 和 `.rodata` 分工不同：`.rodata` 只读 `.data` 可写 */
/* 和 `.bss` 分工不同：`.data` 有初值占文件空间 `.bss` 无初值不占 */

/* 对应的 `Shdr` */
Elf64_Shdr shdr_data = {
    .sh_name      = offset_of(".data"),                 /* 节名 */
    .sh_type      = SHT_PROGBITS,                       /* 程序定义的内容 */
    .sh_flags     = SHF_ALLOC | SHF_WRITE,              /* 占内存 + 可写 */
    .sh_addr      = 0x4000,                             /* 虚拟地址 */
    .sh_offset    = 0x3000,                             /* 文件偏移 */
    .sh_size      = 0x10,                               /* 大小 16 字节 */
    .sh_link      = 0,
    .sh_info      = 0,
    .sh_addralign = 8,                                  /* 8 字节对齐 */
    .sh_entsize   = 0,                                  /* 非表节 */
};

/* 文件里的样子：连续排列的已初始化数据 */
文件偏移 0x3000:
    .data[0]:  0x0000002a    /* g_count = 42 */
    .data[4]:  0x00000000
    .data[8]:  0x00000001    /* g_flag = 1 */
    .data[12]: 0x00000000
```

```c
int g_count = 42;          /* 有初值 放 `.data` */
static int g_flag = 1;     /* 有初值 放 `.data` */
int g_zero = 0;            /* 初值为 0 通常放 `.bss` 不放 `.data` */
/* 把所有有初值的全局 静态变量收集起来 */
/* 生成 `.data` 段放进 `.o` 文件 */
/* 链接器把所有 `.o` 的 `.data` 段合并 */
/* 生成最终可执行文件的 `.data` 节 */
```

```c
/* 数据布局举例 */
/* C 代码 */
int g_count = 42;
int g_flag = 1;

/* 编译后 `.data` 里的样子 */
.data:
    g_count:  .long 42       /* 4 字节 */
    g_flag:   .long 1        /* 4 字节 */

/* 程序里访问 `g_count` */
/* 非 `PIE` 直接 `mov eax, [0x4000]` */
/* `PIE` 先 `lea rax, [rip + 偏移]` 再 `mov eax, [rax]` */

/* 和 `.rodata` 的区别 */
/* 项目       `.rodata`            `.data` */
/* 内容       只读常量 字符串      有初值全局变量 */
/* 权限       `R--`                `RW-` */
/* 可写       否                   是 */
/* 例子       `"hello"` `3.14`     `int g = 42` */

/* 和 `.bss` 的区别 */
/* 项目       `.data`              `.bss` */
/* 初值       有 存在文件里         无 文件中不占空间 */
/* 节类型     `SHT_PROGBITS`       `SHT_NOBITS` */
/* 文件大小   有实际内容            0 只有 `sh_size` */
/* 加载时     从文件读初值          内核清零 */
/* 例子       `int g = 42`         `int g;` */

```

#### .symtab

```c
/* `.symtab`：Symbol Table 全部符号表 */
/* 本质是一个 `Elf64_Sym` 数组 每个元素 24 字节 */
/* 记录文件里所有符号：函数 全局变量 静态符号 节符号 文件名 */
/* 和 `.dynsym` 分工不同：`.dynsym` 运行时用 `.symtab` 调试链接用 */
/* 字符串在 `.strtab` */

/* 对应的 `Shdr` */
Elf64_Shdr shdr_symtab = {
    .sh_name      = offset_of(".symtab"),               /* 节名 */
    .sh_type      = SHT_SYMTAB,                         /* 全部符号表 */
    .sh_flags     = 0,                                  /* 不占内存 不加载 */
    .sh_addr      = 0,                                  /* 没有虚拟地址 */
    .sh_offset    = 0x31e0,                             /* 文件偏移 */
    .sh_size      = 0x300,                              /* 大小 768 字节 = 32 个符号 */
    .sh_link      = 28,                                 /* 关联 `.strtab` 在 SHT 里的索引 */
    .sh_info      = 12,                                 /* 第一个全局符号的下标 */
    .sh_addralign = 8,                                  /* 8 字节对齐 */
    .sh_entsize   = 24,                                 /* 每个 `Elf64_Sym` 24 字节 */
};

/* 每个符号的结构 */
typedef struct {
    uint32_t st_name;   /* 符号名 在 `.strtab` 里的偏移 */
    uint8_t  st_info;   /* 类型 + 绑定 */
    uint8_t  st_other;  /* 可见性 */
    uint16_t st_shndx;  /* 所在节 未定义用 `SHN_UNDEF` */
    uint64_t st_value;  /* 符号地址 */
    uint64_t st_size;   /* 符号大小 */
} Elf64_Sym;

/* 文件里的样子：连续排列的 24 字节条目 */
文件偏移 0x31e0:
    .symtab[0]:  全 0 保留项
    .symtab[1]:  st_name="main.c"     st_info=FILE   st_shndx=ABS
    .symtab[2]:  st_name="read_g"     st_info=FUNC   st_shndx=1  st_value=0x1140
    .symtab[3]:  st_name="g_count"    st_info=OBJECT st_shndx=UND st_value=0
    .symtab[4]:  st_name="g_flag"     st_info=OBJECT st_shndx=8  st_value=0x4020
    ...
```

```c
/* 调试和链接时要知道每个符号的名字 地址 类型 */
/* 链接器靠它做符号解析 合并重复定义 */

/* 和 `.dynsym` 的区别 */
/* 项目       `.symtab`                `.dynsym` */
/* 用途       调试 链接                动态链接 */
/* 运行时     不需要                   必需 */
/* 可 strip   是                       否 */
/* 符号范围   全部符号                 导入导出符号 */
/* 字符串表   `.strtab`                `.dynstr` */
/* 节类型     `SHT_SYMTAB`             `SHT_DYNSYM` */
/* 例子       `main` `read_g` `g_count` `printf` `malloc` */
```

`.symtab` 是全部符号表 调试链接用 可被 strip 有它逆向难度大降

#### .strtab

```c
/* `.strtab`：String Table for .symtab 全部符号的字符串表 */
/* 本质是一个字符串数组 存 `.symtab` 里所有符号的名字 */
/* 每个 `Elf64_Sym` 的 `st_name` 是 `.strtab` 里的偏移 */
/* 和 `.dynstr` 分工不同：`.strtab` 给 `.symtab` 用 `.dynstr` 给 `.dynsym` 用 */
/* 和 `.shstrtab` 分工不同：`.strtab` 存符号名 `.shstrtab` 存节名 */

/* 对应的 `Shdr` */
Elf64_Shdr shdr_strtab = {
    .sh_name      = offset_of(".strtab"),               /* 节名 */
    .sh_type      = SHT_STRTAB,                         /* 字符串表 */
    .sh_flags     = 0,                                  /* 不占内存 不加载 */
    .sh_addr      = 0,                                  /* 没有虚拟地址 */
    .sh_offset    = 0x34e0,                             /* 文件偏移 */
    .sh_size      = 0x1a5,                              /* 大小 */
    .sh_link      = 0,
    .sh_info      = 0,
    .sh_addralign = 1,                                  /* 1 字节对齐 */
    .sh_entsize   = 0,                                  /* 非表节 */
};

/* 文件里的样子：一段字符串 每项以 \0 分隔 */
文件偏移 0x34e0:
    "\0main.c\0read_g\0g_count\0g_flag\0my_constructor\0..."
```

#### .shstrtab

```c
/* `.shstrtab`：Section Header String Table 节名字符串表 */
/* 本质是一个字符串数组 存所有节的名字 */
/* 每个 `Shdr` 的 `sh_name` 是 `.shstrtab` 里的偏移 */
Elf64_Shdr shdr_shstrtab = {
    .sh_name      = offset_of(".shstrtab"),             /* 节名 自己的名字也在里面 */
    .sh_type      = SHT_STRTAB,                         /* 字符串表 */
    .sh_flags     = 0,                                  /* 不占内存 不加载 */
    .sh_addr      = 0,                                  /* 没有虚拟地址 */
    .sh_offset    = 0x303a,                             /* 文件偏移 */
    .sh_size      = 0x1a5,                              /* 大小 */
    .sh_link      = 0,
    .sh_info      = 0,
    .sh_addralign = 1,                                  /* 1 字节对齐 */
    .sh_entsize   = 0,                                  /* 非表节 */
};

/* 文件里的样子：一段字符串 每项以 \0 分隔 */
文件偏移 0x303a:
    "\0.interp\0.note.gnu.property\0.note.gnu.build-id\0"
    ".gnu.hash\0.dynsym\0.dynstr\0.gnu.version\0..."
    "...\0.shstrtab\0"

/* 每个名字在表里的偏移 */
偏移 0    -> ""
偏移 1    -> ".interp"
偏移 9    -> ".note.gnu.property"
偏移 1c   -> ".note.gnu.build-id"
偏移 30   -> ".gnu.hash"
偏移 3a   -> ".dynsym"
偏移 42   -> ".dynstr"
偏移 4a   -> ".gnu.version"
...
偏移 19f  -> ".shstrtab"
```

```c
/* 举例 */
/* `shdr[1].sh_name = 1` */
/* 去 `.shstrtab` 偏移 1 处读 得到 ".interp" */
/* `shdr[2].sh_name = 9` */
/* 去 `.shstrtab` 偏移 9 处读 得到 ".note.gnu.property" */
/* `shdr[3].sh_name = 1c` */
/* 去 `.shstrtab` 偏移 1c 处读 得到 ".note.gnu.build-id" */

/* 链接器 ld 生成节头表时 */
/* 把所有节名收集起来 去重 */
/* 拼成 `.shstrtab` 写进文件 */
/* 然后给每个 `Shdr.sh_name` 填对应偏移 */

/* `ELF Header` 里的 `e_shstrndx` */
/* 存的就是 `.shstrtab` 在 `Section Header Table` 里的索引 */
/* 通常是最后一个节 */

/* 举例 */
e_shstrndx = 29       /* 第 29 个节头是 `.shstrtab` */
/* 读 `shdr[29]` 得到 `.shstrtab` 的文件偏移和大小 */
/* 再去文件偏移处读字符串 */

/* `e_shstrndx` 可以是特殊值 */
SHN_UNDEF     = 0       /* 没有节名表 所有节名读不出来 */
SHN_XINDEX    = 0xffff  /* 真正的索引在 `shdr[0].sh_link` 里 超过 65535 个节时用 */
```

```c
/* 和 `.strtab` `.dynstr` 的区别 */
/* 项目       `.shstrtab`          `.strtab`              `.dynstr` */
/* 用途       节名                 全部符号名             动态符号名 */
/* 谁引用     `Shdr.sh_name`       `.symtab` 的 `st_name` `.dynsym` 的 `st_name` */
/* 运行时     不用                 不用                   运行时必需 */
/* 可 strip   是                   是                     否 */
/* 对应表     无                   无                     `.dynsym` */
/* 入口       `e_shstrndx`         无                     无 */

/* `.shstrtab` 存节名 */
/* `.strtab`  存 `.symtab` 的符号名 */
/* `.dynstr`  存 `.dynsym` 的符号名 还有依赖库名 `DT_NEEDED` */
```

```c
/* 举例：一个完整 ELF 的 `.shstrtab` */
/* 假设文件里有这些节 */
.interp
.note.gnu.property
.note.gnu.build-id
.gnu.hash
.dynsym
.dynstr
.gnu.version
.gnu.version_r
.rela.dyn
.rela.plt
.init
.plt
.text
.fini
.rodata
.eh_frame_hdr
.eh_frame
.init_array
.fini_array
.dynamic
.got
.got.plt
.data
.bss
.comment
.symtab
.strtab
.shstrtab

/* 链接器把这些名字拼成 `.shstrtab` */
/* 每个名字之间用 \0 分隔 */
/* 开头第一个字节是 \0 表示空字符串 */
/* 然后每个 `Shdr.sh_name` 填对应偏移 */
/* 比如 `.text` 的 `Shdr.sh_name` 是 0x1a3 */
/* 去 `.shstrtab` 偏移 0x1a3 处读 得到 ".text" */
```

`.shstrtab` 存所有节的名字 `Shdr.sh_name` 是它的偏移 `e_shstrndx` 指向它 靠它把节的编号翻译成节名

## 加载流程

### load_elf_binary

```c
/* 内核加载 ELF 可执行文件的主函数 */
/* 读 ELF 头 读 Phdr 找 ld.so */
/* 建 VMA 和 ld.so 的 PT_LOAD 段 */
/* 建栈 压启动信息 */
/* 设寄存器跳入口 */

static int load_elf_binary(struct linux_binprm *bprm)

/* `struct linux_binprm`介绍 */
/* 内核里的一个结构体 描述“这次 execve 要执行的程序” */
/* 从 `sys_execve` 到 `load_elf_binary` 全程传递它 */

struct linux_binprm {
    char buf[BINPRM_BUF_SIZE];   /* 文件头 前 256 字节 里面是 Elf64_Ehdr */
    struct file *file;           /* 要执行的文件 */
    unsigned long p;             /* 栈指针 内核压参数时的栈顶 */
    unsigned long argmin;        /* 参数最小地址 */
    unsigned int argc;           /* 参数个数 */
    unsigned int envc;           /* 环境变量个数 */
    const char *filename;        /* 文件名 调试用 */
    struct cred *cred;           /* 进程凭证 */
    int secureexec;              /* 是否 setuid 程序 */
    unsigned long exec;          /* 可执行文件路径字符串地址 */
    //...
};
```

#### 第一步 检查 ELF Header

```c
/* 从 `bprm->buf` 拿到 ELF 头 */
struct elfhdr *elf_ex = (struct elfhdr *)bprm->buf;

/* 检查魔数 */
if (memcmp(elf_ex->e_ident, ELFMAG, SELFMAG) != 0)
    goto out;
/* `ELFMAG` = `0x7f 'E' 'L' 'F'` */
/* 不是 ELF 返回 `-ENOEXEC` */
/* `search_binary_handler` 继续试下一种格式 */

/* 检查文件类型 */
if (elf_ex->e_type != ET_EXEC && elf_ex->e_type != ET_DYN)
    goto out;
/* 只接受 `ET_EXEC` 和 `ET_DYN` */
/* `ET_REL` `ET_CORE` 拒绝 */

/* 检查 CPU 架构 */
if (!elf_check_arch(elf_ex))
    goto out;
/* 必须是 `EM_X86_64` */

/* 检查 FDPIC 嵌入式格式 */
if (elf_check_fdpic(elf_ex))
    goto out;

/* 检查文件能不能 mmap */
if (!can_mmap_file(bprm->file))
    goto out;
/* 普通文件可以 管道 socket 不行 */
```

#### 第二步 读 Program Header

```c
/* 调 `load_elf_phdrs` 读所有 Phdr */
elf_phdata = load_elf_phdrs(elf_ex, bprm->file);
if (!elf_phdata)
    goto out;

/* 内部检查 `e_phentsize` 是不是 56 */
if (elf_ex->e_phentsize != sizeof(struct elf_phdr))
    goto out;
/* 检查总大小 */
size = sizeof(struct elf_phdr) * elf_ex->e_phnum;
if (size == 0 || size > 65536)
    goto out;
/* 分配内核内存 */
elf_phdata = kmalloc(size, GFP_KERNEL);
/* 从文件读 `e_phoff` 处的 `size` 字节 */
retval = elf_read(elf_file, elf_phdata, size, elf_ex->e_phoff);
/* 返回 `elf_phdata` 是 Phdr 数组在内核内存的副本 */
/* `elf_read` 内部调 `kernel_read` */
```

#### 第三步 遍历找 PT_INTERP

```c
/* 遍历所有 Phdr 找 `PT_INTERP` */
elf_ppnt = elf_phdata;
for (i = 0; i < elf_ex->e_phnum; i++, elf_ppnt++) {
    char *elf_interpreter;

    /* 先记录 `PT_GNU_PROPERTY` 后面用 */
    if (elf_ppnt->p_type == PT_GNU_PROPERTY) {
        elf_property_phdata = elf_ppnt;
        continue;
    }

    /* 只找 `PT_INTERP` */
    if (elf_ppnt->p_type != PT_INTERP)
        continue;

    /* 检查路径长度 */
    if (elf_ppnt->p_filesz > PATH_MAX || elf_ppnt->p_filesz < 2)
        goto out_free_ph;

    /* 分配内存读路径字符串 */
    elf_interpreter = kmalloc(elf_ppnt->p_filesz, GFP_KERNEL);

    /* 从文件读解释器路径 */
    retval = elf_read(bprm->file, elf_interpreter, elf_ppnt->p_filesz,
                      elf_ppnt->p_offset);

    /* 必须以 `\0` 结尾 */
    if (elf_interpreter[elf_ppnt->p_filesz - 1] != '\0')
        goto out_free_interp;

    /* 打开 `ld.so` 文件 */
    interpreter = bprm_open_interpreter(bprm, elf_interpreter);
    kfree(elf_interpreter);

    /* 分配内存放 `ld.so` 的 ELF 头 */
    interp_elf_ex = kmalloc_obj(*interp_elf_ex);

    /* 读 `ld.so` 的 ELF 头 */
    retval = elf_read(interpreter, interp_elf_ex,
                      sizeof(*interp_elf_ex), 0);

    break;
}
/* 没有 `PT_INTERP` 说明是静态链接 跳过这步 */
/* 有的话 `interpreter` 指向 `ld.so` 文件 */
```

#### 第四步 遍历找 PT_GNU_STACK 和 arch 段

```c
/* 再遍历一次 找 `PT_GNU_STACK` 和 arch 段 */
elf_ppnt = elf_phdata;
for (i = 0; i < elf_ex->e_phnum; i++, elf_ppnt++)
    switch (elf_ppnt->p_type) {
    case PT_GNU_STACK:
        /* 看有没有 `PF_X` 决定栈是否可执行 */
        if (elf_ppnt->p_flags & PF_X)
            executable_stack = EXSTACK_ENABLE_X;
        else
            executable_stack = EXSTACK_DISABLE_X;
        break;

    case PT_LOPROC ... PT_HIPROC:
        /* 架构特定段 默认啥都不做 */
        retval = arch_elf_pt_proc(elf_ex, elf_ppnt,
                                  bprm->file, false,
                                  &arch_state);
        break;
    }
/* `PT_GNU_STACK` 决定栈是否可执行 */
/* 有 `PF_X` 栈可执行 没有则不可执行 */
/* 现代程序都不让栈可执行 防栈溢出 */
/* `executable_stack` 后面传给 `setup_arg_pages` */
```

#### 第五步 检查ld.so的ELF头

```c
if (interpreter) {
    /* 检查 `ld.so` 魔数 */
    if (memcmp(interp_elf_ex->e_ident, ELFMAG, SELFMAG) != 0)
        goto out_free_dentry;

    /* 检查 `ld.so` 架构 */
    if (!elf_check_arch(interp_elf_ex) ||
        elf_check_fdpic(interp_elf_ex))
        goto out_free_dentry;

    /* 读 `ld.so` 的 Program Header */
    interp_elf_phdata = load_elf_phdrs(interp_elf_ex, interpreter);

    /* 遍历 `ld.so` 的 Phdr 找 arch 特定段 */
    elf_ppnt = interp_elf_phdata;
    for (i = 0; i < interp_elf_ex->e_phnum; i++, elf_ppnt++)
        switch (elf_ppnt->p_type) {
        case PT_GNU_PROPERTY:
            elf_property_phdata = elf_ppnt;
            break;

        case PT_LOPROC ... PT_HIPROC:
            retval = arch_elf_pt_proc(interp_elf_ex, elf_ppnt,
                                      interpreter, true, &arch_state);
            break;
        }
}
/* 检查 `ld.so` 也是合法 ELF */
/* 读 `ld.so` 的 Phdr 存到 `interp_elf_phdata` */
/* 后面映射 `ld.so` 时要用 */
```

#### 第六步 解析 GNU 属性

```c
/* 解析 `PT_GNU_PROPERTY` 段 */
retval = parse_elf_properties(interpreter ?: bprm->file,
                              elf_property_phdata, &arch_state);

/* `PT_GNU_PROPERTY` 里有 CET IBT SHSTK 等安全特性 */
/* 解析结果存到 `arch_state` */
/* x86-64 默认啥都不做 */

/* 给架构最后一次机会拒绝 */
retval = arch_check_elf(elf_ex, !!interpreter, interp_elf_ex,
                        &arch_state);
/* `parse_elf_properties` 解析 GNU 属性 */
/* `arch_check_elf` 架构最后检查 */
/* x86-64 默认都通过 */
```

#### 第七步 清理旧进程 设 personality

```c
/* 刷新旧的可执行文件痕迹 */
retval = begin_new_exec(bprm);
if (retval)
    goto out_free_dentry;
/* `begin_new_exec` 释放旧进程 mm 信号 文件等 */

/* 设 personality 和 arch_state */
SET_PERSONALITY2(*elf_ex, &arch_state);
if (elf_read_implies_exec(*elf_ex, executable_stack))
    current->personality |= READ_IMPLIES_EXEC;

/* 快照 randomize_va_space 决定是否 ASLR */
const int snapshot_randomize_va_space = READ_ONCE(randomize_va_space);
if (!(current->personality & ADDR_NO_RANDOMIZE) && snapshot_randomize_va_space)
    current->flags |= PF_RANDOMIZE;

/* 设新进程 */
setup_new_exec(bprm);

/* 建栈 VMA 压参数环境变量字符串 */
retval = setup_arg_pages(bprm, randomize_stack_top(STACK_TOP),
                         executable_stack);
/* `begin_new_exec` 清理旧进程 */
/* `SET_PERSONALITY2` 设 personality */
/* `PF_RANDOMIZE` 开启 ASLR */
/* `setup_arg_pages` 建栈 VMA */
/* 这一步调完 `bprm->p` 可用 栈已经建好 */
```

#### 第八步 核心循环 映射所有 PT_LOAD

```c
/* 初始化段边界变量 */
elf_brk = 0;
/* 堆起始地址 初始 0 */
/* 后面取所有 PT_LOAD 段里最高的结束地址 */
/* 堆从这往上长 */

start_code = ~0UL;
/* 代码段起始地址 初始是最大值 0xffffffffffffffff */
/* 后面遇到代码段取 min 变成最小地址 */
/* 为什么初始最大 因为后面用 min 更新 */

end_code = 0;
/* 代码段结束地址 初始 0 */
/* 后面取 max 变成最大地址 */

start_data = 0;
/* 数据段起始地址 */

end_data = 0;
/* 数据段结束地址 */

/* 这一步是整个 load_elf_binary 的核心 */
/* 前面都是准备工作 这一步真正建 VMA */
/* 遍历所有 PT_LOAD 段 每个段建一个 VMA */
/* 建 VMA 只占虚拟地址 不分配物理内存 */
/* 物理内存后面程序跑起来缺页才分配 */

/* i 是循环计数 从 0 到 e_phnum - 1 */
/* elf_ppnt 是指针 指向当前 Phdr */
/* 每次循环 elf_ppnt++ 指向下一个 Phdr */
/* elf_phdata 是 Phdr 数组在内核内存的首地址 */
/* elf_ex->e_phnum 是 Phdr 数量 比如 13 */
for(i = 0, elf_ppnt = elf_phdata;
    i < elf_ex->e_phnum; i++, elf_ppnt++) {
    int elf_prot, elf_flags;
    /* elf_prot 是 mmap 权限 PROT_READ/WRITE/EXEC */
    /* elf_flags 是 mmap 标志 MAP_PRIVATE/FIXED 等 */

    unsigned long k, vaddr;
    /* k 是临时变量 记录地址 */
    /* vaddr 是当前段的虚拟地址 */

    unsigned long total_size = 0;
    /* 所有 PT_LOAD 段总大小 */
    /* 只第一个段用 后面清零 */

    unsigned long alignment;
    /* 最大对齐要求 */
    /* 只第一个段用 */

    if (elf_ppnt->p_type != PT_LOAD)
        continue;
    /* 只处理 PT_LOAD 段 */
    /* 其他类型 PT_DYNAMIC PT_INTERP PT_NOTE 全跳过 */
    /* 因为只有 PT_LOAD 需要建 VMA 映射到内存 */

    /* 权限转换 `PF_R/W/X` -> `PROT_READ/WRITE/EXEC` */
    elf_prot = make_prot(elf_ppnt->p_flags, &arch_state,
                         !!interpreter, false);
    /* make_prot 内部 */
    /* 有 PF_R 就设 PROT_READ */
    /* 有 PF_W 就设 PROT_WRITE */
    /* 有 PF_X 就设 PROT_EXEC */
    /* ELF 权限位顺序 X W R 值 1 2 4 */
    /* mmap 权限位顺序 R W X 值 1 2 4 */
    /* 两套编码不一样 要转换 */

    elf_flags = MAP_PRIVATE;
    /* MAP_PRIVATE 私有映射 写时复制 COW */
    /* 多个进程映射同一个文件时 */
    /* 读共享物理页 写时各自复制一份 */
    /* 代码段和数据段都用 MAP_PRIVATE */

    vaddr = elf_ppnt->p_vaddr;
    /* 当前段的虚拟地址 */
    /* 比如代码段 p_vaddr = 0x401000 */
    /* 这是链接时确定的偏移 */
    /* PIE 下这是相对偏移 要加 load_bias */
    /* 非 PIE 下这是绝对地址 load_bias = 0 */

    /* 不是第一个 PT_LOAD 用 MAP_FIXED 固定地址 */
    /* 因为第一个段已经算好 load_bias 了 */
    if (!first_pt_load) {
        elf_flags |= MAP_FIXED;
    /* ET_EXEC 非 PIE 地址固定 */
    } else if (elf_ex->e_type == ET_EXEC) {
        elf_flags |= MAP_FIXED_NOREPLACE;
    /* ET_DYN PIE 需要算 load_bias */
    } else if (elf_ex->e_type == ET_DYN) {
        /* 计算所有 PT_LOAD 总大小 */
        total_size = total_mapping_size(elf_phdata,
                                        elf_ex->e_phnum);
        if (!total_size) {
            retval = -EINVAL;
            goto out_free_dentry;
        }
        /* 计算最大对齐 */
        alignment = maximum_alignment(elf_phdata, elf_ex->e_phnum);
        /* 有 ld.so 的 PIE 可执行文件 */
        if (interpreter) {
            load_bias = ELF_ET_DYN_BASE;
            if (current->flags & PF_RANDOMIZE)
                load_bias += arch_mmap_rnd();   /* ASLR 随机偏移 */
            if (alignment)
                load_bias &= ~(alignment - 1);  /* 对齐 */
            elf_flags |= MAP_FIXED_NOREPLACE;
        /* 没有 ld.so 的静态 PIE */
        } else {
            if (alignment > ELF_MIN_ALIGN) {
                /* 先映射到 0 看内核给哪 */
                load_bias = elf_load(bprm->file, 0, elf_ppnt,
                                     elf_prot, elf_flags, total_size);
                if (BAD_ADDR(load_bias)) {
                    retval = IS_ERR_VALUE(load_bias) ?
                             PTR_ERR((void*)load_bias) : -EINVAL;
                    goto out_free_dentry;
                }
                vm_munmap(load_bias, total_size);  /* 再取消 */
                if (alignment)
                    load_bias &= ~(alignment - 1);
                elf_flags |= MAP_FIXED_NOREPLACE;
            } else
                load_bias = 0;
        }
        /* 减去第一个 vaddr 对齐到页 */
        load_bias = ELF_PAGESTART(load_bias - vaddr);
    }
    /* 整个函数最复杂的部分 三种情况 */
    /* 非第一个 PT_LOAD 用 MAP_FIXED 因为第一个已经算好 load_bias */
    /* ET_EXEC 非 PIE 地址固定 不需要随机化 */
    /* ET_DYN PIE 有 interpreter 从 ELF_ET_DYN_BASE 加 ASLR */
    /* 没有 interpreter 是静态 PIE 先映射看内核给哪再对齐 */

    /* 关键 真正建 VMA 映射当前段 */
    error = elf_load(bprm->file, load_bias + vaddr, elf_ppnt,
                     elf_prot, elf_flags, total_size);
    /* elf_load 内部调 elf_map */
    /* elf_map 内部调 vm_mmap */
    /* vm_mmap 内部调 mmap_region */
    /* mmap_region 里 vm_area_alloc 分配 VMA 结构体 */
    /* vma_link 挂到 mm_struct 的链表和红黑树 */
    /* 建 VMA 只占虚拟地址 不分配物理内存 */
    /* 物理内存等程序访问触发缺页才分配 */
    /* 参数 load_bias + vaddr 是真实虚拟地址 */
    if (BAD_ADDR(error)) {
        retval = IS_ERR_VALUE(error) ?
                 PTR_ERR((void*)error) : -EINVAL;
        goto out_free_dentry;
    }
    if (first_pt_load) {
        first_pt_load = 0;
        if (elf_ex->e_type == ET_DYN) {
            /* 第一个段映射后调整 load_bias */
            /* error 是实际映射到的地址 */
            /* ELF_PAGESTART(load_bias + vaddr) 是请求的地址 */
            /* 差值 = 实际比请求偏了多少 */
            /* 加到 load_bias 上修正 后面段用修正值 */
            load_bias += error -
                         ELF_PAGESTART(load_bias + vaddr);
            reloc_func_desc = load_bias;
        }
    }

    /* 找出包含 Program Header 的段 */
    if (elf_ppnt->p_offset <= elf_ex->e_phoff &&
        elf_ex->e_phoff < elf_ppnt->p_offset + elf_ppnt->p_filesz) {
        phdr_addr = elf_ex->e_phoff - elf_ppnt->p_offset +
                    elf_ppnt->p_vaddr;
        /* phdr_addr 是 Program Header 在内存里的地址 */
        /* 后面填 AT_PHDR */
    }

    /* 更新段边界 */
    k = elf_ppnt->p_vaddr;
    if ((elf_ppnt->p_flags & PF_X) && k < start_code)
        start_code = k;
    /* 是代码段 更新 start_code 取最小 */

    if (start_data < k)
        start_data = k;
    /* 更新 start_data 取最大 */

    /* 检查是否超出 TASK_SIZE */
    if (BAD_ADDR(k) || elf_ppnt->p_filesz > elf_ppnt->p_memsz ||
        elf_ppnt->p_memsz > TASK_SIZE ||
        TASK_SIZE - elf_ppnt->p_memsz < k) {
        retval = -EINVAL;
        goto out_free_dentry;
    }
    /* BAD_ADDR 检查地址是否超出用户空间 */
    /* p_filesz 不能大于 p_memsz */
    /* p_memsz 不能超过 TASK_SIZE */
    /* 段结束地址不能超 TASK_SIZE */

    k = elf_ppnt->p_vaddr + elf_ppnt->p_filesz;
    if ((elf_ppnt->p_flags & PF_X) && end_code < k)
        end_code = k;
    /* 是代码段 更新 end_code 取最大 */

    if (end_data < k)
        end_data = k;
    /* 更新 end_data 取最大 */

    k = elf_ppnt->p_vaddr + elf_ppnt->p_memsz;
    if (k > elf_brk)
        elf_brk = k;
    /* 更新 elf_brk 取所有段里最高结束地址 */
}
```

#### 第九步 加 load_bias 修正所有地址

```c
e_entry = elf_ex->e_entry + load_bias;
phdr_addr += load_bias;
elf_brk += load_bias;
start_code += load_bias;
end_code += load_bias;
start_data += load_bias;
end_data += load_bias;
/* 之前算的是相对地址 */
/* 加上 `load_bias` 得到真实运行地址 */
/* 非 PIE `load_bias = 0` 不变 */
/* PIE `load_bias` 是随机基址 */
```

#### 第十步 加载ld.so或直接用主程序入口

```c
if (interpreter) {
    /* 有 ld.so 加载它 */
    elf_entry = load_elf_interp(interp_elf_ex,
                                interpreter,
                                load_bias, interp_elf_phdata,
                                &arch_state);
    /* load_elf_interp 映射 ld.so 的 PT_LOAD 段 */
    /* 返回 ld.so 加载基址 */
    /* 内部和主程序一样 遍历 PT_LOAD 建 VMA */
    /* 但加载到高地址区 不和主程序冲突 */
    if (!IS_ERR_VALUE(elf_entry)) {
        interp_load_addr = elf_entry;              /* ld.so 基址 */
        elf_entry += interp_elf_ex->e_entry;       /* ld.so 入口 */
    }
    /* interp_load_addr 后面填 AT_BASE */
    /* elf_entry 最终是 ld.so 入口地址 */

    if (BAD_ADDR(elf_entry)) {
        retval = IS_ERR_VALUE(elf_entry) ?
                (int)elf_entry : -EINVAL;
        goto out_free_dentry;
    }
    reloc_func_desc = interp_load_addr;
    /* 关闭 ld.so 文件 */
    exe_file_allow_write_access(interpreter);
    fput(interpreter);
    /* ld.so 已经映射到内存 不需要再读文件 */

    kfree(interp_elf_ex);
    kfree(interp_elf_phdata);
    /* 释放 ld.so 的 ELF 头和 Phdr 内存 */
} else {
    /* 静态链接 直接用主程序入口 */
    elf_entry = e_entry;
    if (BAD_ADDR(elf_entry)) {
        retval = -EINVAL;
        goto out_free_dentry;
    }
}

kfree(elf_phdata);
/* 释放主程序 Phdr 内存 用完了 */

set_binfmt(&elf_format);
/* 记录当前进程用 ELF 格式 */

#ifdef ARCH_HAS_SETUP_ADDITIONAL_PAGES
    retval = ARCH_SETUP_ADDITIONAL_PAGES(bprm, elf_ex, !!interpreter);
    if (retval < 0)
        goto out;
#endif
/* x86-64 不定义 跳过 */
```

#### 第十一步 建栈 填 auxv

```c
/* 建栈 压 `argc` `argv` `envp` `auxv` */
retval = create_elf_tables(bprm, elf_ex, interp_load_addr,
                           e_entry, phdr_addr);
if (retval < 0)
    goto out;
/* 这就是之前详细讲过的 `create_elf_tables` */
/* 参数 */
/* `interp_load_addr` 填 `AT_BASE` */
/* `e_entry` 填 `AT_ENTRY` */
/* `phdr_addr` 填 `AT_PHDR` */
/* 执行完 `bprm->p` 是最终栈顶 */
```

#### 第十二步 更新 mm_struct

```c
mm = current->mm;
mm->end_code = end_code;
mm->start_code = start_code;
mm->start_data = start_data;
mm->end_data = end_data;
mm->start_stack = bprm->p;
/* 把段边界记录到 `mm_struct` */
/* `start_stack` 是栈顶 */
/* `/proc/pid/stat` 读这些 */

elf_coredump_set_mm_eflags(mm, elf_ex->e_flags);
/* 记录 `e_flags` 后面 coredump 用 */
```

#### 第十三步 设 brk

```c
/* 静态 PIE 把 brk 移到 ELF_ET_DYN_BASE */
if (!IS_ENABLED(CONFIG_COMPAT_BRK) &&
    IS_ENABLED(CONFIG_ARCH_HAS_ELF_RANDOMIZE) &&
    elf_ex->e_type == ET_DYN && !interpreter) {
    elf_brk = ELF_ET_DYN_BASE;
    brk_moved = true;
}
mm->start_brk = mm->brk = ELF_PAGEALIGN(elf_brk);
/* brk 是堆起始位置 */
/* 等于所有段中最高的结束地址页对齐 */

/* ASLR 随机化 brk */
if ((current->flags & PF_RANDOMIZE) && snapshot_randomize_va_space > 1) {
    if (!brk_moved)
        mm->brk = mm->start_brk = mm->brk + PAGE_SIZE;
    mm->brk = mm->start_brk = arch_randomize_brk(mm);
    brk_moved = true;
}
/* ASLR 开启时 堆起始再加随机偏移 */
/* 堆和栈之间留随机空隙 防攻击 */
/* 兼容 MMAP_PAGE_ZERO */
if (current->personality & MMAP_PAGE_ZERO) {
    error = vm_mmap(NULL, 0, PAGE_SIZE, PROT_READ | PROT_EXEC,
                    MAP_FIXED | MAP_PRIVATE, 0);
    if (!error)
        mseal_mmap_page_zero();
}
/* 兼容很老的程序 现代程序不设这个 */
```

#### 第十四步 设寄存器跳入口

```c
regs = current_pt_regs();
/* 拿当前进程的寄存器结构 */

#ifdef ELF_PLAT_INIT
    ELF_PLAT_INIT(regs, reloc_func_desc);
#endif
/* x86-64 不定义 跳过 */

finalize_exec(bprm);
/* 最后的收尾工作 */

START_THREAD(elf_ex, regs, elf_entry, bprm->p);
/* 关键 设寄存器 跳入口 */
/* 宏 实际是 `start_thread` */
/* 参数 */
/* `regs` 寄存器结构 */
/* `elf_entry` 入口地址 填 `rip` */
/* `bprm->p` 栈顶 填 `rsp` */

/* `start_thread` 干这些 */
regs->ip = elf_entry;    /* `rip` = 入口 */
regs->sp = bprm->p;      /* `rsp` = 栈顶 */
regs->cs = __USER_CS;    /* 代码段 */
regs->ss = __USER_DS;    /* 数据段 */

retval = 0;
out:
    return retval;
/* 函数返回 内核 `sys_execve` 结束 */
/* `iretq` 回用户态 */
/* `rip` 指向 `ld.so` 或主程序入口 */
```

#### 完整流程总结

```c
/* 1  检查 ELF Header */
/* 2  读 Program Header */
/* 3  遍历找 PT_INTERP */
/* 4  遍历找 PT_GNU_STACK 和 arch 段 */
/* 5  检查 ld.so 的 ELF 头 */
/* 6  解析 GNU 属性 */
/* 7  清理旧进程 设 personality */
/* 8  核心循环 映射所有 PT_LOAD */
/* 9  加 load_bias 修正所有地址 */
/* 10 加载 ld.so 或直接用主程序入口 */
/* 11 建栈 填 auxv */
/* 12 更新 mm_struct */
/* 13 设 brk */
/* 14 设寄存器跳入口 */

/* 关键子函数 */
/* `load_elf_phdrs` 读 Phdr */
/* `elf_load` -> `elf_map` -> `vm_mmap` -> `mmap_region` 建 VMA */
/* `load_elf_interp` 映射 ld.so */
/* `create_elf_tables` 建栈 */
/* `start_thread` 设寄存器跳入口 */
```

### 动态链接

`load_elf_binary` 结束的那一刻，进程的虚拟地址空间里只有三样东西，主程序的几个 `PT_LOAD` 段，`ld.so` 的几个 `PT_LOAD` 段，还有栈

物理内存一页都没分配，页表是空的，等程序访问的时候触发缺页才分配

`start_thread` 设好了寄存器，`rip` 指向 `ld.so` 入口，`rsp` 指向栈顶，然后内核 `sys_execve` 返回，执行 `iretq`，`CPU` 从内核态切回用户态，从 `rip` 处开始执行

`CPU` 执行的第一条指令在 `ld.so` 里 `_dl_start`，其次 `ld.so` 自己处理重定位相关

接着 `ld.so` 从栈上读 `auxv`，拿到`AT_PHDR`(主程序 `Program Header` 的虚拟地址)，`AT_BASE`(`ld.so` 自己的加载基址)，`AT_ENTRY` (主程序入口)

`ld.so` 找到主程序的 `Program Header`之后遍历找到 `PT_DYNAMIC`，得到主程序 `.dynamic` 的虚拟地址，读 `.dynamic` 里的 `DT_NEEDED`，找到依赖库的名字

然后 `ld.so` 按 `DT_NEEDED` 逐个加载依赖库，搜索路径按顺序来，`DT_RPATH` `LD_LIBRARY_PATH` 环境变量 `DT_RUNPATH` `/etc/ld.so.cache` `/lib` 和 `/usr/lib`，找到库文件后，读它的 `ELF` 头和 `Program Header`，把它的 `PT_LOAD` 段 `mmap` 到 `mmap` 区，每个库建一个 `link_map` 结构，串成链表

加载完依赖库后，`ld.so` 做符号解析，把所有库的 `.dynsym` 收集起来建全局符号表，然后重定位，修正 `GOT` 等，让程序能访问外部符号

重定位做完后，`ld.so` 调依赖库的 `.init_array`，它遍历 `link_map` 链表，对每个依赖库调它的 `.init_array` 里的函数，再调它的 `DT_INIT`，顺序是先依赖的库后自己，这些是编译器生成的构造函数，主程序的 `.init_array` 不在这里调，由 `__libc_start_main` 调

最后 `ld.so` 读 `AT_ENTRY` 拿到主程序入口地址，设好寄存器 `rdi` = `argc` `rsi` = `argv` `rdx` = `envp`，跳转到主程序的 `e_entry` 也就是 `_start`

然后 `_start` 开始跑，`_start` 由 `crt1.o` 提供，链接时自动加进去，它先从栈顶 `pop rsi` 得到 `argc`，把 `rsp` 存到 `rdx` 作为 `argv`，然后调 `__libc_start_main`，参数包括 `main` 函数地址 `argc` `argv` `init` 函数 `fini` 函数 `rtld_fini`

`__libc_start_main` 开始干这些事，保存 `rtld_fini`，调 `__libc_setup_tls` 初始化线程局部存储，建 `TLS` 块，设置 `fs` 段寄存器，调 `__libc_init_first` 初始化 `libc` 内部状态，比如 `errno` `stdio`，调 `__libc_csu_init`，`__libc_csu_init` 遍历主程序的 `.init_array`，逐个调用主程序的构造函数，再调主程序的 `DT_INIT`，注册 `atexit` 回调，最后调 `main(argc argv envp)`，用户的 `main` 函数开始执行

到这一步 `mmap` 区里已经有 `ld.so` `libc` `libm` 等，主程序段在低地址，栈在高地址，堆还没有

`main` 里第一次调 `malloc` 的时候，`glibc` 发现堆是空的，调 `brk` 系统调用，内核收到 `brk`，从之前设好的 `start_brk` 开始建堆 `VMA`，堆 `VMA` 在数据段后面，权限 `RW`，`malloc` 从这里切一块内存给用户，如果 `malloc` 要更多内存，`glibc` 再调 `brk` 抬高 `brk`，堆 `VMA` 跟着扩展

顺便，`glibc` 的 `malloc` 分配超过 `128KB` 的内存，不走 `brk` 堆，直接 `mmap` 一块匿名内存放这里

```c
/* 完整布局 从高地址到低地址 */
高地址 0x7fffffffffff
    ┌─────────────────────┐
    │ 内核空间             │  用户不能访问
    ├─────────────────────┤
    │ 栈                  │  从高往低长
    │   ↓↓↓ 向下增长       │  rsp 往下移
    │   局部变量 返回地址   │
    │   参数 环境变量       │
    ├─────────────────────┤
    │ 空闲                 │  栈和 mmap 之间
    ├─────────────────────┤
    │ mmap 区             │  共享库 大块 malloc
    │   libc.so           │
    │   ld.so             │
    │   大块 malloc        │
    ├─────────────────────┤
    │ 空闲                 │  堆和 mmap 之间
    ├─────────────────────┤
    │ 堆                  │  从低往高长
    │   ↑↑↑ 向上增长       │  brk 往上移
    │   malloc 分配的东西   │
    ├─────────────────────┤  brk <- 堆顶 当前用到哪
    │                     │  start_brk <- 堆起始
    ├─────────────────────┤
    │ .bss                │  未初始化全局变量
    ├─────────────────────┤
    │ .data               │  已初始化全局变量
    ├─────────────────────┤
    │ .rodata             │  只读数据
    ├─────────────────────┤
    │ .text               │  代码
    ├─────────────────────┤
    │ ELF 头              │
低地址 0x400000
```
