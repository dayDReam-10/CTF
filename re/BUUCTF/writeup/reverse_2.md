 
# RE_2 Writeup

---

## 分析过程

1. 照常 ida 打开
2. 选择 `ELF64 for x86-64 (Executable) [elf.dll]`
3. <kbd>Shift</kbd> + <kbd>F12</kbd> 查找到 `"this is the right flag!"`
4. <kbd>Ctrl</kbd> + <kbd>F5</kbd> → <kbd>Enter</kbd> → <kbd>F5</kbd> 追踪

## 反编译结果

```c
int __fastcall main(int argc, const char **argv, const char **envp)
{
  int stat_loc; // [rsp+4h] [rbp-3Ch] BYREF
  int i; // [rsp+8h] [rbp-38h]
  __pid_t pid; // [rsp+Ch] [rbp-34h]
  char s2[24]; // [rsp+10h] [rbp-30h] BYREF
  unsigned __int64 v8; // [rsp+28h] [rbp-18h]

  v8 = __readfsqword(0x28u);
  pid = fork();
  if ( pid )
  {
    waitpid(pid, &stat_loc, 0);
  }
  else
  {
    // "{hacking_for_fun}"
    for ( i = 0; i <= strlen(flag); ++i )
    {
      if ( flag[i] == 105 || flag[i] == 114 )   // "{hacking_for_fun}"
        flag[i] = 49;                           // "{hacking_for_fun}"
    }
  }
  printf("input the flag:");
  __isoc99_scanf("%20s", s2);
  if ( !strcmp(
          flag,                                 // "{hacking_for_fun}"
          s2) )
    return puts("this is the right flag!");
  else
    return puts("wrong flag!");
}
```

## 解题

与上一题差不多思路，不细讲，去查询 asc `105` `114` `49` 轻松得到答案

> `flag{hack1ng_fo1_fun}`