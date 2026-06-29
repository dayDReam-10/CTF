# reverse_1

## 文件判断

观察到样本是 `.exe` 结尾

## 加载方式

选择 `Portable executable for AMD64 (PE) [pe.dll]` 打开

## 分析步骤

1. 打开后先查字符串，按 `Shift + F12` 进入 Strings 窗口
2. 按 `Ctrl + F` 搜索关键字 `flag`
3. 发现包含 `flag` 的字符串共三处
4. 双击目标字符串，跳转到 `.rdata` 段
5. 按 `Ctrl + X` `Enter` 查看交叉引用
6. 按 `F5` 反编译为伪 C 代码

```c
int __fastcall main_0(int argc, const char **argv, const char **envp)
{
  char *v3; // rdi
  __int64 i; // rcx
  size_t MaxCount; // rax
  char v7; // [rsp+0h] [rbp-20h] BYREF
  int j; // [rsp+24h] [rbp+4h]
  char Str1[224]; // [rsp+48h] [rbp+28h] BYREF
  __int64 j_1; // [rsp+128h] [rbp+108h]

  v3 = &v7;
  for ( i = 82; i; --i )
  {
    *(_DWORD *)v3 = -858993460;
    v3 += 4;
  }
  for ( j = 0; ; ++j )
  {
    j_1 = j;
    if ( j > j_strlen(Str2) )                   // "{hello_world}"
      break;
    if ( Str2[j] == 111 )                       // "{hello_world}"
      Str2[j] = 48;                             // "{hello_world}"
  }
  sub_1400111D1("input the flag:");
  sub_14001128F("%20s", Str1);
  MaxCount = j_strlen(Str2);                    // "{hello_world}"
  if ( !strncmp(
          Str1,
          Str2,                                 // "{hello_world}"
          MaxCount) )
    sub_1400111D1("this is the right flag!\n");
  else
    sub_1400111D1("wrong flag\n");
  return 0;
}
```

> 查看代码发现要获得正确的flag需要分析

```c
 if ( !strncmp(
          Str1,
          Str2,                                 // "{hello_world}"
          MaxCount) )
    sub_1400111D1("this is the right flag!\n");
```

猜测 `strncmp` 是做字符串比较的，故最后的 Str1 是 `{hello_world}`，但是 Str1 只有 `sub_14001128F("%20s", Str1);` 处理过

所以我们分析 Str2，观察到处理 Str2 的逻辑出现在：

```c
  for ( j = 0; ; ++j )
  {
    j_1 = j;
    if ( j > j_strlen(Str2) )                   // "{hello_world}"
      break;
    if ( Str2[j] == 111 )                       // "{hello_world}"
      Str2[j] = 48;                             // "{hello_world}"
  }
```

**显然是一个遍历字符串处理，而且是对于 ASCII=111 的处理换成 48（o->0）所以 Str2 的 o->0 即可（注意 `{hello_world}` 是最初声明的值，后续处理注释不会变化）**

