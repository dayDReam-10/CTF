# SimpleRev Writeup

## 1. 源代码逻辑

```c
unsigned __int64 Decry()
{
  char char; // [rsp+Fh] [rbp-51h]
  int v2; // [rsp+10h] [rbp-50h]
  int v3; // [rsp+14h] [rbp-4Ch]
  int i; // [rsp+18h] [rbp-48h]
  int i_1; // [rsp+1Ch] [rbp-44h]
  char src[8]; // [rsp+20h] [rbp-40h] BYREF
  __int64 v7; // [rsp+28h] [rbp-38h]
  int v8; // [rsp+30h] [rbp-30h]
  _QWORD v9[2]; // [rsp+40h] [rbp-20h] BYREF
  int v10; // [rsp+50h] [rbp-10h]
  unsigned __int64 v11; // [rsp+58h] [rbp-8h]

  v11 = __readfsqword(0x28u);
  *(_QWORD *)src = 0x534C43444ELL;
  v7 = 0;
  v8 = 0;
  v9[0] = 0x776F646168LL;
  v9[1] = 0;
  v10 = 0;
  text = (char *)join(
                   key3,                        // "kills"
                   v9);
  strcpy(key, key1);                            // "ADSFK"
  strcat(key, src);
  v2 = 0;
  v3 = 0;
  getchar();
  i_1 = strlen(key);
  for ( i = 0; i < i_1; ++i )
  {
    if ( key[v3 % i_1] > 64 && key[v3 % i_1] <= 90 )
      key[i] = key[v3 % i_1] + 32;
    ++v3;
  }
  printf("Please input your flag:");
  while ( 1 )
  {
    char = getchar();
    if ( char == 10 )
      break;
    if ( char == 32 )
    {
      ++v2;
    }
    else
    {
      if ( char <= 96 || char > 122 )
      {
        if ( char > 64 && char <= 90 )
        {
          str2[v2] = (char - 39 - key[v3 % i_1] + 97) % 26 + 97;
          ++v3;
        }
      }
      else
      {
        str2[v2] = (char - 39 - key[v3 % i_1] + 97) % 26 + 97;
        ++v3;
      }
      if ( !(v3 % i_1) )
        putchar(32);
      ++v2;
    }
  }
  if ( !strcmp(text, str2) )
    puts("Congratulation!\n");
  else
    puts("Try again!\n");
  return __readfsqword(0x28u) ^ v11;
}
```

易得：
* **string key = "adsfkndcls"**
* **string text = "killshadow"**

从而我们的 `input_char` 的集合也要是 `text`。

---

## 2. 核心分析：两种解题方法

接下来是关键，有两种方法：

### 方法 1：由于数据范围不大，直接 py 爆破
但我觉得爆破太没脑子了，也认识不到这种移位逆向的本质。

### 方法 2：移位取模逆向数学解
于是我想了一个下午，想出一个数学的直接的反向取模方法。

首先 `str2-97` (密文位置偏移量 $t$) 回到循环圆盘的原点，用偏移量加常数代替加密过程（因为移位本质上就是偏移量的变化）。

**加密过程分析：**
加密公式为：`str2[v2] = (char - 39 - key[v3 % i_1] + 97) % 26 + 97`

1. 首先是 `str2[i] - 97` ($t$) 回到原点。
2. `char` 化为偏移量加起点 $\rightarrow char = c + 65$。
3. `key` 同理 (注意 `char` 和 `key` 的起点)。

**代数推导：**
$$t = (c + 65 - 39 - (k + 97) + 97) \pmod{26}$$
$$t = (c + 26 - k) \pmod{26}$$
$$t = (c - k) \pmod{26}$$

**解得反向映射：**
$$c = (t + k) \pmod{26}$$

### 解密实现 (C++)
```cpp
#include <bits/stdc++.h> 
using namespace std;

int main(){
    string key = "adsfkndcls";
    int v3=10;
    int i_1 = key.length();
  // for (int i = 0; i < i_1; ++i )
  // {
  //   if ( key[v3 % i_1] > 64 && key[v3 % i_1] <= 90 )
  //     key[i] = key[v3 % i_1] + 32;
  //   ++v3;
  // }
  // cout << key << endl;
  // cout<< v3<<endl;

  string text = "killshadow";
  for(int i = 0; i < text.length(); ++i)
  {
    int t = text[i] - 97;
    int k = key[i] - 97;
    int c = (t + k) % 26;
    text[i] = c + 65; // (注意这个65!这个是大写的起点！)
  }
  cout << text << endl;   
}
```

---

## 3. 题目逻辑疑点总结

但是我们回看这个题目，其实我觉得有点问题。请看这一段：

```c
      if ( char <= 96 || char > 122 )
      {
        if ( char > 64 && char <= 90 )
        {
          str2[v2] = (char - 39 - key[v3 % i_1] + 97) % 26 + 97;
          ++v3;
        }
      }
      else
      {
        str2[v2] = (char - 39 - key[v3 % i_1] + 97) % 26 + 97;
        ++v3;
      }
```

**发现了吗？不论大小写！都变成小写了。。。**

经过尝试是全大写。

**即 flag{KLDQCUDFZO}**

---
