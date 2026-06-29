# Happy New Year Writeup

---

## 分析过程

依旧先用 IDA 打开题目程序，并按 exe 的常规方式加载。

加载后很快能发现异常：

- 函数名很少
- <kbd>Shift</kbd> + <kbd>F12</kbd> 几乎没有有效字符串
- 关键函数点一遍也找不到明显线索

这类现象通常说明程序被加壳了。

为了确认壳的类型，可以使用 DIE（Detect It Easy）检测，结果表明样本使用了 UPX 壳。关键信息如下：

```text
PE32
操作系统: Windows(95) [I386, 32位, 控制台]
链接程序: GNU Linker Id (GNU Binutils) (2.22)
编译器: MinGW (Heur)
语言: C
打包工具: UPX (3.91) [NRV, best] (Heur)
附加信息: Compressed or packed data
```

## 脱壳

把文件放到 Kali 中，使用 UPX 进行脱壳：

```bash
upx -d 新年快乐.exe -o A.exe
```

输出如下：

```text
                       Ultimate Packer for eXecutables
                          Copyright (C) 1996 - 2024
UPX 4.2.4       Markus Oberhumer, Laszlo Molnar & John Reiser    May 9th 2024

        File size         Ratio      Format      Name
   --------------------   ------   -----------   -----------
     27807 <-     21151   76.06%    win32/pe     A.exe

Unpacked 1 file.
```

说明脱壳成功，接下来分析生成的 A.exe 即可。

## 反编译

将 A.exe 再次拖入 IDA，可以看到可读信息明显增多。

这次依旧通过字符串定位，追踪 `this is true flag!`，可以得到主逻辑：

```c
int __cdecl main(int argc, const char **argv, const char **envp)
{
  char Str2[14]; // [esp+12h] [ebp-3Ah] BYREF
  char Str1[44]; // [esp+20h] [ebp-2Ch] BYREF

  __main();
  strcpy(Str2, "HappyNewYear!");
  memset(Str1, 0, 32);
  printf("please input the true flag:");
  scanf("%s", Str1);
  if ( !strncmp(Str1, Str2, strlen(Str2)) )
    return puts("this is true flag!");
  else
    return puts("wrong!");
}
```

## 解题

从这段代码可以直接看出：

- `strcpy(Str2, "HappyNewYear!")` 将正确字符串写入 `Str2`
- 程序随后使用 `strncmp(Str1, Str2, strlen(Str2))` 比较输入和 `Str2`

也就是说，用户输入的 flag 内容本身就是 `HappyNewYear!`。

题目答案为：

> `HappyNewYear!`

如果需要补上常见的 flag 外壳，则可写作：

> `flag{HappyNewYear!}`