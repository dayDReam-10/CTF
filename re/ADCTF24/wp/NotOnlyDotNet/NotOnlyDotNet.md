# NotOnlyDotNet WriteUp

## 题目概述

（dump内存，zstd解压，代码分析）

主函数给出，直接分析

```c
int __fastcall main(int argc, const char **argv, const char **envp)
{
  void *p_stat_loc; // rsi
  __int64 v4; // rdx
  __int64 v5; // rcx
  __int64 v6; // r8
  __int64 v7; // r9
  char *s_2; // [rsp+0h] [rbp-E0h]
  char *s_3; // [rsp+8h] [rbp-D8h]
  __int64 v11; // [rsp+10h] [rbp-D0h]
  char s[64]; // [rsp+20h] [rbp-C0h] BYREF
  char _tmp_tmpdir.XXXX[32]; // [rsp+60h] [rbp-80h] BYREF
  char *file[4]; // [rsp+80h] [rbp-60h] BYREF
  char s_1[8]; // [rsp+A4h] [rbp-3Ch] BYREF
  int stat_loc; // [rsp+ACh] [rbp-34h] BYREF
  int pipedes[2]; // [rsp+B0h] [rbp-30h] BYREF
  __pid_t pid; // [rsp+B8h] [rbp-28h]
  int v19; // [rsp+BCh] [rbp-24h]
  FILE *stream; // [rsp+C0h] [rbp-20h]
  void *ptr; // [rsp+C8h] [rbp-18h]
  size_t size; // [rsp+D0h] [rbp-10h]
  char *v23; // [rsp+D8h] [rbp-8h]

  qmemcpy(_tmp_tmpdir.XXXX, "/tmp/tmpdir.XXXX", 16);
  *(_DWORD *)&_tmp_tmpdir.XXXX[15] = (_DWORD)&unk_585858;
  v23 = mkdtemp(_tmp_tmpdir.XXXX);
  if ( !v23 )
  {
    perror("mkdtemp");
    exit(1);
  }
  sprintf(s, "%s/shell", v23);
  size = ZSTD_getFrameContentSize(&gshell_data, (unsigned int)gshell_size);
  ptr = malloc(size);
  size = ZSTD_decompress(ptr, size, &gshell_data, (unsigned int)gshell_size);
  if ( (unsigned int)ZSTD_isError(size) )
  {
    perror("ZSTD_decompress");
    exit(1);
  }
  stream = fopen(s, "w");
  fwrite(ptr, size, 1u, stream);
  fclose(stream);
  free(ptr);
  v19 = chmod(s, 0x1C0u);
  if ( v19 == -1 )
  {
    perror("chmod");
    exit(1);
  }
  size = ZSTD_getFrameContentSize(&gcore_data, (unsigned int)gcore_size);
  ptr = malloc(size);
  size = ZSTD_decompress(ptr, size, &gcore_data, (unsigned int)gcore_size);
  if ( (unsigned int)ZSTD_isError(size) )
  {
    perror("ZSTD_decompress");
    exit(1);
  }
  if ( pipe(pipedes) == -1 )
  {
    perror("pipe");
    exit(1);
  }
  pid = fork();
  if ( pid < 0 )
  {
    perror("fork");
    exit(1);
  }
  if ( pid <= 0 )
  {
    close(pipedes[1]);
    sprintf(s_1, "%d", pipedes[0]);
    s_2 = s;
    s_3 = s_1;
    v11 = 0;
    file[0] = s;
    file[1] = s_1;
    file[2] = 0;
    p_stat_loc = file;
    execvp(s, file);
  }
  else
  {
    close(pipedes[0]);
    write(pipedes[1], ptr, size);
    close(pipedes[1]);
    free(ptr);
    p_stat_loc = &stat_loc;
    waitpid(pid, &stat_loc, 0);
  }
  v19 = rmdir_all(v23, p_stat_loc, v4, v5, v6, v7, s_2, s_3, v11);
  if ( v19 == -1 )
  {
    perror("rmdir_all");
    exit(1);
  }
  return 0;
}
```

## 关键信息

遇到了ZSTD的相关函数

```c
size = ZSTD_decompress(ptr, size, &gcore_data, (unsigned int)gcore_size);

size = ZSTD_decompress(ptr, size, &gshell_data, (unsigned int)gshell_size);
```

先不着急，先分析下主逻辑

首先shell_data放到s里面了

core_data通过管道传给子进程

所以我们要知道这两数据

直接点击跟踪看看地址和值dump就行

.rodata:00000000004044D0 28                                gshell_data 
.rodata:0000000001FE1160 80 CC BD 01                       gshell_size dd 1BDCC80h 

.rodata:0000000000402010 28                                gcore_data 
.rodata:00000000004044C0 AA 24 00 00                       gcore_size dd 24AAh     

找完了

## 导出数据

shift+f2 换py写脚本

```python
import idaapi
import idc
import ida_bytes

start = 0x4044D0
size = 0x1BDCC80

data=ida_bytes.get_bytes(start,size)

with open("shell_data.bin", "wb") as f:
    f.write(data)

import idaapi
import idc
import ida_bytes

start = 0x402010
size = 0x24AA

data=ida_bytes.get_bytes(start,size)

with open("core_data.bin", "wb") as f:
    f.write(data)
```

## 解压分析

然后用zstd解压

再用ilspy打开

容易分析是aes+xor+base64呀

反过来写脚本就好啦

```python
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
```