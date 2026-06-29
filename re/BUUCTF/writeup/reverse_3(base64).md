# Reverse_3 Writeup

照常ida打开 shift+f12追踪flag字符串，追到main函数得到

```c
int __cdecl main_0(int argc, const char **argv, const char **envp)
{
  size_t v3; // eax
  const char *Source; // eax
  size_t MaxCount; // eax
  char v7; // [esp+0h] [ebp-188h]
  char v8; // [esp+0h] [ebp-188h]
  signed int j; // [esp+DCh] [ebp-ACh]
  int i; // [esp+E8h] [ebp-A0h]
  signed int j_1; // [esp+E8h] [ebp-A0h]

  sub_411375("%20s", (char)Str);
  v3 = j_strlen(Str);
  Source = (const char *)sub_4110BE(Str, v3, v14);
  strncpy(Destination, Source, 0x28u);
  j_1 = j_strlen(Destination);
  for ( j = 0; j < j_1; ++j )
    Destination[j] += j;
  MaxCount = j_strlen(Destination);
  if ( !strncmp(
          Destination,
          Str2,                                 // "e3nifIH9b_C@n@dH"
          MaxCount) )
    sub_41132F("rigth flag!\n", v8);
  else
    sub_41132F("wrong flag!\n", v8);
  return 0;
}
```

看函数内部

```c
  if ( !strncmp(
          Destination,
          Str2,                                 // "e3nifIH9b_C@n@dH"
          MaxCount) )
    sub_41132F("rigth flag!\n", v8);
```

通过比较得到

Destination="e3nifIH9b_C@n@dH"；

再看遍历的处理逻辑

```c
  for ( j = 0; j < j_1; ++j )
    Destination[j] += j;
```

比较简单反向减掉就行

记这个减去之后的为 Destination1

再根据

strncpy(Destination, Source, 0x28u);

 得到Source是 Destination1

由  Source = (const char *)sub_4110BE(Str, v3, v14);

知source又是来源于函数sub_4110BE

那我们点进去看看sub_4110BE

```c
// attributes: thunk
int __cdecl sub_4110BE(char *Str, size_t a2, _BYTE *a3)
{
  return sub_411AB0(Str, a2, a3);
}
```

有个跳板，没事继续追

```c
void *__cdecl sub_411AB0(char *Str, size_t a2, _BYTE *a3)
{
  int v4; // [esp+D4h] [ebp-38h]
  int v5; // [esp+D4h] [ebp-38h]
  int v6; // [esp+D4h] [ebp-38h]
  int v7; // [esp+D4h] [ebp-38h]
  int i; // [esp+E0h] [ebp-2Ch]
  size_t v9; // [esp+ECh] [ebp-20h]
  int v10; // [esp+ECh] [ebp-20h]
  int v11; // [esp+ECh] [ebp-20h]
  void *v12; // [esp+F8h] [ebp-14h]
  char *Str_1; // [esp+104h] [ebp-8h]

  v9 = a2;
  v11 = a2;
  if ( (int)(a2 / 3) % 3 )
    v10 = 4 * (a2 / 3 + 1);
  else
    v10 = 4 * v9;
  v12 = malloc(v10 + 1);
  if ( !v12 )
    return 0;
  Str_1 = Str;
  v4 = 0;
  while ( 1 )
  {
    for ( i = 0; i < 3 && v11 >= 1; ++i )
    {
      byte_41A144[i] = *Str_1;
      --v11;
      ++Str_1;
    }
    if ( !i )
      break;
    switch ( i )
    {
      case 1:
        *((_BYTE *)v12 + v4) = aAbcdefghijklmn[(int)(unsigned __int8)byte_41A144[0] >> 2];
        v5 = v4 + 1;
        *((_BYTE *)v12 + v5) = aAbcdefghijklmn[((algn_41A145[0] & 0xF0) >> 4) | (16 * (byte_41A144[0] & 3))];
        *((_BYTE *)v12 + ++v5) = aAbcdefghijklmn[64];
        *((_BYTE *)v12 + ++v5) = aAbcdefghijklmn[64];
        v4 = v5 + 1;
        break;
      case 2:
        *((_BYTE *)v12 + v4) = aAbcdefghijklmn[(int)(unsigned __int8)byte_41A144[0] >> 2];
        v6 = v4 + 1;
        *((_BYTE *)v12 + v6) = aAbcdefghijklmn[((algn_41A145[0] & 0xF0) >> 4) | (16 * (byte_41A144[0] & 3))];
        *((_BYTE *)v12 + ++v6) = aAbcdefghijklmn[((algn_41A145[1] & 0xC0) >> 6) | (4 * (algn_41A145[0] & 0xF))];
        *((_BYTE *)v12 + ++v6) = aAbcdefghijklmn[64];
        v4 = v6 + 1;
        break;
      case 3:
        *((_BYTE *)v12 + v4) = aAbcdefghijklmn[(int)(unsigned __int8)byte_41A144[0] >> 2];
        v7 = v4 + 1;
        *((_BYTE *)v12 + v7) = aAbcdefghijklmn[((algn_41A145[0] & 0xF0) >> 4) | (16 * (byte_41A144[0] & 3))];
        *((_BYTE *)v12 + ++v7) = aAbcdefghijklmn[((algn_41A145[1] & 0xC0) >> 6) | (4 * (algn_41A145[0] & 0xF))];
        *((_BYTE *)v12 + ++v7) = aAbcdefghijklmn[algn_41A145[1] & 0x3F];
        v4 = v7 + 1;
        break;
    }
  }
  *((_BYTE *)v12 + v4) = 0;
  return v12;
}
```

得到一个很长的逻辑

怎么说呢，根据经验知道这是base64

base64的加密原理是8位切成6位，如11010101 01001010 11010101一共二十四位，3个8位，它被切成四个六位 

得到

110101 010100 101011 010101 再按照base64表格解密

不够位置怎么办？

比如11010101 
切完变成 110101 01
那么第二个数字会补0000

使得变成 110101 010000

这里只有两个字符 怎么输出四个字符呢，base64提供了占位符=

如这里就会输出XY==

由于base64是3位化成4位，而且有一张表，所以还是特征比较明显

比如这里追踪aAbcdefghijklmn得到

ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/

标准base64表

利用cyberchef解就行

### 题解过程

```c
#include <stdio.h>
#include <string.h>

int main()
{

    char Destination[] = "e3nifIH9b_C@n@dH";
    int j_1 = strlen(Destination);

    for (int j = 0; j < j_1; ++j)
    {
        Destination[j] -= j;
    }

    printf("还原后的字符串: %s\n", Destination);

    return 0;
}
```

得到e2lfbDB2ZV95b3V9

放给 cyberchef 得到 {i_l0ve_you}

（这么浪漫...）

加个flag结束

flag{i_l0ve_you}