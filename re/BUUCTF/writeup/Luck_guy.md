# Luck_guy Writeup

## 1. 题目逻辑分析
通过逆向 `get_flag()` 函数，可以发现 Flag 的获取依赖于对 `f2` 字符串的处理。程序通过 `rand() % 200` 进入不同的 `case`，核心逻辑顺序如下：

1.  **执行 Case 4**：初始化 `f2`。将十六进制常数 `0x7F666F6067756369LL` 赋值给变量 `s`，并拼接至 `f2`。
2.  **执行 Case 5**：数据变换。对 `f2` 数组中的 8 个字节进行特定的算术运算。
3.  **执行 Case 1**：输出结果。拼接 `f1` ("GXY{do_not_") 与处理后的 `f2` 并打印。

### 关键点：字节序（Endianness）
使用 **DIE (Detect It Easy)** 查询可知程序为 **小端序 (Little-Endian)**。这意味着在内存中，`0x7F666F6067756369LL` 的存储顺序是反向的（从低位字节 `69` 开始）。

---

## 2. 算法还原
根据代码逻辑，`f2` 的变换规则如下：
* 当索引 $j$ 为奇数时：`*(&f2 + j) -= 2`
* 当索引 $j$ 为偶数时：`--*(&f2 + j)`（即减 1）

---

## 3. 解题脚本 (C)

```c
#include <stdio.h>
#include <string.h>

int main()
{
    // 1. 数据准备
    long long s = 0x7F666F6067756369LL;
    char f2[9] = {0}; // 准备 9 字节，留一个位置给字符串结束符 \0

    // 2. 将 long long 按字节拷贝进字符数组 (自动处理 LE 顺序)
    memcpy(f2, &s, 8);

    // 3. 按照 case 5 的逻辑进行变换
    for (int j = 0; j <= 7; ++j)
    {
        if (j % 2 == 1)
        {
            f2[j] -= 2; 
        }
        else
        {
            f2[j] -= 1; 
        }
    }

    // 4. 打印结果
    printf("f2 处理结果: %s\n", f2);
    
    // 打印十六进制用于调试
    printf("Hex 序列: ");
    for(int i=0; i<8; i++) printf("%02X ", (unsigned char)f2[i]);
    
    return 0;
}
```
得到结果："hate_me}"
---

## 4. 最终结果
* **f1**: `GXY{do_not_`
* **f2 (计算得出)**: `hate_me}`
* **Flag**: `GXY{do_not_hate_me}`

