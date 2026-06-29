# xor Writeup

## 1. 初步分析

照常打开ida  
字符串查询追踪

得到 main

```c
int __fastcall main(int argc, const char **argv, const char **envp)
{
  int i; // [rsp+2Ch] [rbp-124h]
  char __b[264]; // [rsp+40h] [rbp-110h] BYREF

  memset(__b, 0, 0x100u);
  printf("Input your flag:\n");
  get_line(__b, 256);
  if ( strlen(__b) != 33 )
    goto LABEL_7;
  for ( i = 1; i < 33; ++i )
    __b[i] ^= __b[i - 1];
  if ( !strncmp(
          __b,
          global,                               // "f\nk\fw&O.@\x11x\rZ;U\x11p\x19F\x1Fv\"M#D\x0Eg\x06h\x0FG2O"
          0x21u) )
    printf("Success");
  else
LABEL_7:
    printf("Failed");
  return 0;
}
```

## 2. 重命名变量

有点难看，先把__b改名为flag

```c
int __fastcall main(int argc, const char **argv, const char **envp)
{
  int i; // [rsp+2Ch] [rbp-124h]
  char flag[264]; // [rsp+40h] [rbp-110h] BYREF

  memset(flag, 0, 0x100u);
  printf("Input your flag:\n");
  get_line(flag, 256);
  if ( strlen(flag) != 33 )
    goto LABEL_7;
  for ( i = 1; i < 33; ++i )
    flag[i] ^= flag[i - 1];
  if ( !strncmp(
          flag,
          global,                               // "f\nk\fw&O.@\x11x\rZ;U\x11p\x19F\x1Fv\"M#D\x0Eg\x06h\x0FG2O"
          0x21u) )
    printf("Success");
  else
LABEL_7:
    printf("Failed");
  return 0;
}
```

## 3. 关键逻辑与坑点

细看代码，处理flag的段落只有

```c
  for ( i = 1; i < 33; ++i )
    flag[i] ^= flag[i - 1];
```

并知道结果是

```text
f\nk\fw&O.@\x11x\rZ;U\x11p\x19F\x1Fv\"M#D\x0Eg\x06h\x0FG2O
```

但是有坑，直接按顺着编写脚本解是错误的，仔细想想xor的执行过程？

假设 1 2 3 三个字符 2xor1得到4 此时下一位3是去用4去做异或的！即假设3加密后是5 5等于(3xor(2xor1))

所以我们要逆向求解 编写脚本记得用py, cpp要防止贪婪解析 比较复杂

```cpp
#include <bits/stdc++.h>

using namespace std;

int main()
{
    std::string flag = "f\nk\fw&O.@\x11x\rZ;U\x11p\x19"
                    "F\x1Fv\"M#D\x0Eg\x06h\x0FG2O";
    for (int i = 32; i >= 1; i--)
        flag[i] ^= flag[i - 1];
    cout << flag << endl;
}
```

## 4. 最终结果

得到flag{QianQiuWanDai_YiTongJiangHu}