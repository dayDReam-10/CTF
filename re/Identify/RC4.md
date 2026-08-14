# RC4

## 算法原理

RC4 是一种流密码，根据密钥打乱 256 字节 S 盒，再不断生成伪随机密钥流，最后和明文/密文逐字节异或。加密和解密是同一个函数

### 1. Key Scheduling Algorithm(KSA)

即密钥调度算法

```c
void rc4_init(uint8_t *S, const uint8_t *key, size_t keylen) {
    int i, j = 0;

    for (i = 0; i < 256; i++) {
        S[i] = i;
    }//init 常做指纹识别

    for (i = 0; i < 256; i++) {
        j = (j + S[i] + key[i % keylen]) & 0xFF;//由密钥决定的交换
        uint8_t tmp = S[i];
        S[i] = S[j];
        S[j] = tmp;//swap
    }
}
```

### 2. Pseudo-Random Generation Algorithm(PRGA)

即伪随机生成算法

```c
void rc4_crypt(uint8_t *S, uint8_t *data, size_t len) {//这里的len是data的
    int i = 0, j = 0;

    while (len--) {
        //PRGA：更新索引并继续洗牌
        i = (i + 1) & 0xFF;
        j = (j + S[i]) & 0xFF;

        uint8_t tmp = S[i];
        S[i] = S[j];
        S[j] = tmp;

        // 生成密钥流字节并异或
        uint8_t t = (S[i] + S[j]) & 0xFF;
        *data++ ^= S[t];
    }
}
```

我们发现到核心过程是一个对流密钥的异或，所以我们的解密也很简单，再次调用`PRGA`即可

```c
void rc4_decrypt(uint8_t *S, uint8_t *data, size_t len, const uint8_t *key, size_t keylen) {
    rc4_init(S, key, keylen);
    rc4_crypt(S, data, len);
}
```

## 识别特征

逆向时可通过以下结构特征认出 RC4：

- **初始化指纹**：256 次循环的 `S[i] = i`，把 S 盒顺序填成 0~255
- **KSA 交换**：`j = (j + S[i] + key[i % keylen]) & 0xFF` 之后 `swap(S[i], S[j])`
- **PRGA 密钥流**：`t = (S[i] + S[j]) & 0xFF`，再 `data ^= S[t]`
- **取模方式**：全程 `& 0xFF`（等价 `% 256`）
- **密钥循环复用**：`key[i % keylen]` 周期性取密钥字节

## TIPS

**Q1:**不想写脚本有什么办法快速出答案吗

**A:**选择Cyberchef就好，不过注意是否魔改

**Q2:**存在什么魔改方式吗

**A:**`Sbox`的非标准化，如果算法简单，直接copy或者自己重写就好，如果比较难看，可以选择动调下断点`dump`出来，`KSA`的魔改等等也是可以抄一次的，如果 `PRGA` 也被魔改了，比如丢弃前 N 个密钥流字节，或索引更新公式变化，同样照着原逻辑抄一遍，别自己推，容易出错
