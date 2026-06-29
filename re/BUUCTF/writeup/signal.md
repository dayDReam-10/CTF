#青龙杯 signal Writeup

vm题，就是模拟电脑操作而已，这题甚至算不上什么vm，纯纯模拟题吧

跟踪主函数

int __cdecl main(int argc, const char **argv, const char **envp)
{
  int dst[117]; // [esp+18h] [ebp-1D4h] BYREF

  __main();
  qmemcpy(dst, &src_, 0x1C8u);
  vm_operad(dst, 114);
  puts("good,The answer format is:flag {}");
  return 0;
}
先注意下端序问题，点击src_可以看看，所以这里才是0x1C8对应114

看看vm_operad

int __cdecl vm_operad(int *dst, int n114)
{
  int n114_2; // eax
  char Str[200]; // [esp+13h] [ebp-E5h] BYREF
  char v4; // [esp+DBh] [ebp-1Dh]
  int v5; // [esp+DCh] [ebp-1Ch]
  int v6; // [esp+E0h] [ebp-18h]
  int v7; // [esp+E4h] [ebp-14h]
  int v8; // [esp+E8h] [ebp-10h]
  int n114_1; // [esp+ECh] [ebp-Ch]

  n114_1 = 0;
  v8 = 0;
  v7 = 0;
  v6 = 0;
  v5 = 0;
  while ( 1 )
  {
    n114_2 = n114_1;
    if ( n114_1 >= n114 )
      return n114_2;
    switch ( dst[n114_1] )
    {
      case 1:
        Str[v6 + 100] = v4;
        ++n114_1;
        ++v6;
        ++v8;
        break;
      case 2:
        v4 = dst[n114_1 + 1] + Str[v8];
        n114_1 += 2;
        break;
      case 3:
        v4 = Str[v8] - LOBYTE(dst[n114_1 + 1]);
        n114_1 += 2;
        break;
      case 4:
        v4 = dst[n114_1 + 1] ^ Str[v8];
        n114_1 += 2;
        break;
      case 5:
        v4 = dst[n114_1 + 1] * Str[v8];
        n114_1 += 2;
        break;
      case 6:
        ++n114_1;
        break;
      case 7:
        if ( Str[v7 + 100] != dst[n114_1 + 1] )
        {
          printf("what a shame...");
          exit(0);
        }
        ++v7;
        n114_1 += 2;
        break;
      case 8:
        Str[v5] = v4;
        ++n114_1;
        ++v5;
        break;
      case 10:
        read(Str);
        ++n114_1;
        break;
      case 11:
        v4 = Str[v8] - 1;
        ++n114_1;
        break;
      case 12:
        v4 = Str[v8] + 1;
        ++n114_1;
        break;
      default:
        continue;
    }
  }
}

我们挨个分析吧 

case 1 

Str[v6+100]被赋值

case 2 3 4 5 

是对v4的处理

case 6

只处理了下标

case 7 

检查

case 8


