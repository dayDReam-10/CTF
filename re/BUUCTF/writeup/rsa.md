# RSA Writeup

我们先了解 **RSA 的加密原理**：

## 1. 密钥生成
1. 选取两个大质数 $p$ 和 $q$，计算 $n = p \times q$。
2. 计算欧拉函数 $\varphi(n) = (p-1)(q-1)$。
3. 选择一个与 $\varphi(n)$ 互质的整数 $e$，作为公钥指数（常用 $e=65537$）。
4. 计算 $d$，使得 $e \times d \equiv 1 \pmod{\varphi(n)}$，即 $d$ 是 $e$ 关于 $\varphi(n)$ 的乘法逆元。
5. 公钥为 $(n, e)$，私钥为 $(n, d)$。

## 2. 加密过程
将明文 $m$加密为密文 $c$：
$$c = m^e \bmod n$$

## 3. 解密过程
用私钥将密文 $c$ 解密还原为明文 $m$：
$$m = c^d \bmod n$$

---

### 第一步：获取参数

所以我们要解出 **e n d**

首先拿到 **publickey**：

```text
-----BEGIN PUBLIC KEY-----
MDwwDQYJKoZIhvcNAQEBBQADKwAwKAIhAMAzLFxkrkcYL2wch21CM2kQVFpY9+7+
/AvKr1rzQczdAgMBAAE=
-----END PUBLIC KEY-----
```

用 **ssl解析**：[http://www.hiencode.com/pub_asys.html](http://www.hiencode.com/pub_asys.html)

得到：
- **e** = `65537`
- **n** = `86934482296048119190666062003494800588905656017203025617216654058378322103517`

---

### 第二步：大数分解

接下来求 **phin**，但是求 **phin** 要 **p, q**。

利用在线素数分解网站：[http://www.factordb.com/](http://www.factordb.com/)

得到：
- **p** = `285960468890451637935629440372639283459`
- **q** = `304008741604601924494328155975272418463`

求得 **phin**。接下来有 **e phin** 可以求得 **d**。接下来有 **d c n** 可以解出 **明文 m**。

---

### 第三步：编写解密脚本

利用 **py脚本** 求解就好：

```python
import gmpy2
import rsa

# 初始化参数
e = 65537
n = 86934482296048119190666062003494800588905656017203025617216654058378322103517
p = 285960468890451637935629440372639283459
q = 304008741604601924494328155975272418463

# 计算欧拉函数
phin = (q - 1) * (p - 1)

# 求逆元 d
d = gmpy2.invert(e, phin)

# 构造私钥
key = rsa.PrivateKey(n, e, int(d), p, q)

# 读取并解密
with open("D:\\你的路径\\flag.enc", "rb+") as f:
    f_content = f.read()

flag = rsa.decrypt(f_content, key)
print(flag)
```
flag{decrypt_256}
```


