# Luck_guy (动态调试) Writeup 

练习动调

练习下 elf的动调(pwn_dbg)

ida先看主函数

```c
int __fastcall main(int argc, const char **argv, const char **envp)
{
  unsigned int v4; // [rsp+14h] [rbp-Ch] BYREF
  unsigned __int64 v5; // [rsp+18h] [rbp-8h]

  v5 = __readfsqword(0x28u);
  welcome(argc, argv, envp);
  puts("_________________");
  puts("try to patch me and find flag");
  v4 = 0;
  puts("please input a lucky number");
  __isoc99_scanf("%d", &v4);
  patch_me(v4);
  puts("OK,see you again");
  return 0;
}
```

跟踪patch_me(v4)

```c
int __fastcall patch_me(int a1)
{
  if ( a1 % 2 == 1 )
    return puts("just finished");
  else
    return get_flag();
}
```

知道唯有输入偶数才能进入get_flag()

```c
unsigned __int64 get_flag()
{
  unsigned int seed; // eax
  int i; // [rsp+4h] [rbp-3Ch]
  int j; // [rsp+8h] [rbp-38h]
  __int64 s; // [rsp+10h] [rbp-30h] BYREF
  char v5; // [rsp+18h] [rbp-28h]
  unsigned __int64 v6; // [rsp+38h] [rbp-8h]

  v6 = __readfsqword(0x28u);
  seed = time(0);
  srand(seed);
  for ( i = 0; i <= 4; ++i )
  {
    switch ( rand() % 200 )
    {
      case 1:
        puts("OK, it's flag:");
        memset(&s, 0, 0x28u);
        strcat((char *)&s, f1);                 // "GXY{do_not_"
        strcat((char *)&s, &f2);
        printf("%s", (const char *)&s);
        break;
      case 2:
        printf("Solar not like you");
        break;
      case 3:
        printf("Solar want a girlfriend");
        break;
      case 4:
        s = 0x7F666F6067756369LL;
        v5 = 0;
        strcat(&f2, (const char *)&s);
        break;
      case 5:
        for ( j = 0; j <= 7; ++j )
        {
          if ( j % 2 == 1 )
            *(&f2 + j) -= 2;
          else
            --*(&f2 + j);
        }
        break;
      default:
        puts("emmm,you can't find flag 23333");
        break;
    }
  }
  return __readfsqword(0x28u) ^ v6;
}
```

显然执行逻辑是 4 5 1 

显然我们需要rand()%200的结果是 4 5 1

放wsl里面利用pwn_dbg 动调

首先 disass get_flag 

```asm
   0x00000000004007cb <+0>:     push   rbp
   0x00000000004007cc <+1>:     mov    rbp,rsp
   0x00000000004007cf <+4>:     sub    rsp,0x40
   0x00000000004007d3 <+8>:     mov    rax,QWORD PTR fs:0x28
   0x00000000004007dc <+17>:    mov    QWORD PTR [rbp-0x8],rax
   0x00000000004007e0 <+21>:    xor    eax,eax
   0x00000000004007e2 <+23>:    mov    edi,0x0
   0x00000000004007e7 <+28>:    call   0x400660 <time@plt>
   0x00000000004007ec <+33>:    mov    edi,eax
   0x00000000004007ee <+35>:    call   0x400650 <srand@plt>
   0x00000000004007f3 <+40>:    mov    DWORD PTR [rbp-0x3c],0x0
   0x00000000004007fa <+47>:    jmp    0x400979 <get_flag+430>
   0x00000000004007ff <+52>:    call   0x400690 <rand@plt>
   0x0000000000400804 <+57>:    mov    ecx,eax
```

   注意到这些

   显然我们要处理这个eax 

   ok 打下断点

```gdb
   pwndbg> b *   0x0000000000400804
Breakpoint 1 at 0x400804

c执行到断点

观看反汇编

b► 0x400804 <get_flag+57>    mov    ecx, eax                        ECX => 0x5d20f6de
   0x400806 <get_flag+59>    mov    edx, 0x51eb851f                 EDX => 0x51eb851f
   0x40080b <get_flag+64>    mov    eax, ecx                        EAX => 0x5d20f6de
   0x40080d <get_flag+66>    imul   edx
   0x40080f <get_flag+68>    sar    edx, 6
   0x400812 <get_flag+71>    mov    eax, ecx                        EAX => 0x5d20f6de
   0x400814 <get_flag+73>    sar    eax, 0x1f
   0x400817 <get_flag+76>    sub    edx, eax                        EDX => 0x77346f (0x77346f - 0x0)
   0x400819 <get_flag+78>    mov    eax, edx                        EAX => 0x77346f
   0x40081b <get_flag+80>    mov    dword ptr [rbp - 0x34], eax     [0x7fffffffdbec] <= 0x77346f
   0x40081e <get_flag+83>    mov    eax, dword ptr [rbp - 0x34]     EAX, [0x7fffffffdbec] => 0x77346f
```

这里我们直接set $eax =4 然后c

再 set 5 c执行

再 set 1 c

```text
00:0000│ rsp 0x7fffffffdbe0 ◂— 0x300000000
01:0008│-038 0x7fffffffdbe8 ◂— 0x100000008
02:0010│-030 0x7fffffffdbf0 ◂— 'GXY{do_not_hate_me}'
03:0018│-028 0x7fffffffdbf8 ◂— 'ot_hate_me}'
04:0020│-020 0x7fffffffdc00 ◂— 0x7d656d /* 'me}' */
05:0028│-018 0x7fffffffdc08 ◂— 0
06:0030│-010 0x7fffffffdc10 ◂— 0
07:0038│-008 0x7fffffffdc18 ◂— 0x2d1ab95c4e644a00
```

由于 printf 缺少换行符导致输出被缓冲，Flag 并未直接打印在屏幕上，但已存储在栈上局部变量 s 中（[rbp-0x30]）

看栈内部分，得到答案

GXY{do_not_hate_me}

