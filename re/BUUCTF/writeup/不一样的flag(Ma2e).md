# 不一样的flag Writeup

## 1. 基础检查
die查壳，发现没有壳后，照常ida打开。

## 2. 核心代码逻辑
得到如下伪代码：

```c
int __cdecl __noreturn main(int argc, const char **argv, const char **envp)
{
  _BYTE road[29]; // [esp+17h] [ebp-35h] BYREF
  int v4; // [esp+34h] [ebp-18h]
  int n4; // [esp+38h] [ebp-14h] BYREF
  int i; // [esp+3Ch] [ebp-10h]
  _BYTE v7[12]; // [esp+40h] [ebp-Ch] BYREF

  __main();
  road[26] = 0;
  *(_WORD*)&road[27] = 0;
  v4 = 0;
  strcpy(road, "*11110100001010000101111#");
  while ( 1 )
  {
    puts("you can choose one action to execute");
    puts("1 up");
    puts("2 down");
    puts("3 left");
    printf("4 right\n:");
    scanf("%d", &n4);
    if ( n4 == 2 )
    {
      ++*(_DWORD *)&road[25];
    }
    else if ( n4 > 2 )
    {
      if ( n4 == 3 )
      {
        --v4;
      }
      else
      {
        if ( n4 != 4 )
LABEL_13:
          exit(1);
        ++v4;
      }
    }
    else
    {
      if ( n4 != 1 )
        goto LABEL_13;
      --*(_DWORD *)&road[25];
    }
    for ( i = 0; i <= 1; ++i )
    {
      if (*(_DWORD *)&road[4* i + 25] > 4u )
        exit(1);
    }
    if ( v7[5 **(_DWORD *)&road[25] - 41 + v4] == 49 )
      exit(1);
    if ( v7[5* *(_DWORD*)&road[25] - 41 + v4] == 35 )
    {
      puts("\nok, the order you enter is the flag!");
      exit(0);
    }
  }
}
```

注意这里我给 `_11110100001010000101111_` 改名为 `road` 了。

---

## 3. 详细分析
先看逻辑。要想拿到flag 必须要进入：
```c
if ( v7[5 **(_DWORD *)&road[25] - 41 + v4] == 35 )
{
  puts("\nok, the order you enter is the flag!");
}
```

同时也不能违反：
```c
if ( *(_DWORD *)&road[4 * i + 25] > 4u )
    exit(1);
if ( v7[5 * *(_DWORD *)&road[25] - 41 + v4] == 49 )
  exit(1);
```

初步来看就是某种处理后不能触碰某一个字符 不能大于一个范围。

我们继续回看 `while ( 1 )`：
```c
  while ( 1 )
  {
    puts("you can choose one action to execute");
    puts("1 up");
    puts("2 down");
    puts("3 left");
    printf("4 right\n:");
    scanf("%d", &n4);
    if ( n4 == 2 )
    {
      ++*(_DWORD *)&road[25];
    }
    else if ( n4 > 2 )
    {
      if ( n4 == 3 )
      {
        --v4;
      }
      else
      {
        if ( n4 != 4 )
LABEL_13:
          exit(1);
        ++v4;
      }
    }
```
这像不像我们的上下左右键位？所以这是一道画图的逆向题！

---

## 4. 迷宫还原与求解
终点是哪里？根据 `if ( v7[5* *(_DWORD*)&road[25] - 41 + v4] == 35 )` 了解到终点是 `#`。

**画图得到：**
```
* 1 1 1 1
0 1 0 0 0
0 1 0 1 0
0 0 0 1 0
1 1 1 1 #
```

由题目的判断：
```c
if ( *(_DWORD *)&road[4 * i + 25] > 4u )
    exit(1);
if ( v7[5 * *(_DWORD *)&road[25] - 41 + v4] == 49 )
  exit(1);
```
知道不能碰到 `1`。

那就很简单了 按着 1234 的作用走一次迷宫就行。
* **1**: up
* **2**: down
* **3**: left
* **4**: right

**解题路径：**
向下3次 -> 向右2次 -> 向上2次 -> 向右2次 -> 向下3次

**最终序列：**
`222441144222`
```