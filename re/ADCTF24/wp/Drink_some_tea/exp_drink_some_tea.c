#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>

// 48字节密文（从 IDA 提取）
unsigned char ciphertext[48] = {
    0x89, 0x11, 0x0B, 0xC2, 0xDE, 0x3A, 0x5D, 0x27,
    0xDE, 0xFC, 0xAD, 0xB1, 0x6D, 0x16, 0x01, 0x82,
    0xDC, 0x08, 0x1E, 0xCD, 0x99, 0x08, 0x83, 0xA0,
    0x06, 0xC7, 0xC8, 0xC7, 0xF5, 0xA9, 0xC9, 0x9F,
    0x1D, 0xA7, 0x50, 0x82, 0x66, 0x9E, 0x32, 0xED,
    0xD7, 0x21, 0x8D, 0xB8, 0x43, 0x3C, 0xDA, 0x2E
};

// 密钥
uint32_t key[4] = {
    0x114514,    // 1131796
    0x1919810,   // 26318864
    0x39C5BB,    // 3786171
    0xFFE211     // 16769553
};

// 解密函数（使用32个元素的随机数数组，第0个为0，无需分支判断）
void tea_decrypt(unsigned int* a1, unsigned int* a2) {
    int i;
    unsigned int v3;  // a1[1]
    unsigned int v4;  // a1[0]
    unsigned int v5;  // sum

    v4 = a1[0];
    v3 = a1[1];

    // 生成随机数序列（32个，第0个为0）
    srand(0x7E8);                 // 2024
    unsigned int randoms[32];
    randoms[0] = 0;               // 第1轮加密没有加随机数
    for (i = 1; i < 32; i++) {
        randoms[i] = rand();      // 第2~32轮分别对应的随机数
    }

    // 正向计算最终sum（加密结束时的v5）
    v5 = 0;
    for (i = 0; i < 32; i++) {
        v5 -= 0x61C88647;         // 相当于 v5 += 0x9E3779B9
        v5 += randoms[i];         // 第0轮加0，其余加对应随机数
    }

    // 解密32轮（正序循环，逆向撤销）
    for (i = 0; i < 32; i++) {
        // 逆后半轮（对应加密的 v4 += ...）
        v3 -= (a2[(v5 >> 11) & 3] + v5) ^ (v4 + ((v4 >> 5) ^ (16 * v4)));

        // 逆sum更新
        v5 += 0x61C88647;          // 撤销 delta
        v5 -= randoms[31 - i];     // 撤销随机数（第i=31时减randoms[0]=0）

        // 逆前半轮（对应加密的 v5 += ...）
        v4 -= (a2[v5 & 3] + v5) ^ (v3 + ((v3 >> 5) ^ (16 * v3)));
    }

    a1[0] = v4;
    a1[1] = v3;
}

int main() {
    // 每8字节一块，共6块
    for (int i = 0; i < 48; i += 8) {
        unsigned int block[2];
        memcpy(block, &ciphertext[i], 8);
        tea_decrypt(block, key);
        memcpy(&ciphertext[i], block, 8);
    }

    printf("Flag: %s\n", ciphertext);
    return 0;
}