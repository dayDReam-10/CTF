#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gdc_decrypt.py — 解密 Godot 加密 .gdc，还原成原生 .gdc

    python gdc_decrypt.py <目录> [输出目录]     默认输出到 <目录>/_decoded
    python gdc_decrypt.py --selftest            只跑 AES 自检

解密出来的明文本身就是合法的 .gdc（GDSC + version + decompressed_size + zstd 帧），
压缩是格式的一部分，不要再解 zstd，否则 GDRE 报 Error decompressing GDScript tokenizer buffer。

纯标准库，不需要 zstd、不需要 node。
"""
import os
import struct
import sys

KEY = bytes.fromhex('ce4df8753b59a5a39ade58ac07ef947a3da39f2af75e3284d51217c04d49a061')

# ---------------------------------------------------------------- AES-256
SBOX = bytes.fromhex(
    '637c777bf26b6fc53001672bfed7ab76'
    'ca82c97dfa5947f0add4a2af9ca472c0'
    'b7fd9326363ff7cc34a5e5f171d83115'
    '04c723c31896059a071280e2eb27b275'
    '09832c1a1b6e5aa0523bd6b329e32f84'
    '53d100ed20fcb15b6acbbe394a4c58cf'
    'd0efaafb434d338545f9027f503c9fa8'
    '51a3408f929d38f5bcb6da2110fff3d2'
    'cd0c13ec5f974417c4a77e3d645d1973'
    '60814fdc222a908846eeb814de5e0bdb'
    'e0323a0a4906245cc2d3ac629195e479'
    'e7c8376d8dd54ea96c56f4ea657aae08'
    'ba78252e1ca6b4c6e8dd741f4bbd8b8a'
    '703eb5664803f60e613557b986c11d9e'
    'e1f8981169d98e949b1e87e9ce5528df'
    '8ca1890dbfe6426841992d0fb054bb16'
)


def _xtime(a):
    a <<= 1
    return (a ^ 0x1B) & 0xFF if a & 0x100 else a


def expand_key(key):
    w = [list(key[i:i + 4]) for i in range(0, 32, 4)]
    rcon = 1
    for i in range(8, 60):
        t = list(w[i - 1])
        if i % 8 == 0:
            t = t[1:] + t[:1]
            t = [SBOX[b] for b in t]
            t[0] ^= rcon
            rcon = _xtime(rcon)
        elif i % 8 == 4:
            t = [SBOX[b] for b in t]
        w.append([w[i - 8][j] ^ t[j] for j in range(4)])
    return w


def encrypt_block(w, block):
    s = [block[i] ^ w[i >> 2][i & 3] for i in range(16)]
    for rnd in range(1, 15):
        s = [SBOX[b] for b in s]
        t = [0] * 16
        for i in range(16):
            c, r = i >> 2, i & 3
            t[i] = s[(((c + r) & 3) << 2) + r]
        s = t
        if rnd != 14:
            for c in range(4):
                i = c << 2
                a0, a1, a2, a3 = s[i], s[i + 1], s[i + 2], s[i + 3]
                x = a0 ^ a1 ^ a2 ^ a3
                s[i] = a0 ^ x ^ _xtime(a0 ^ a1)
                s[i + 1] = a1 ^ x ^ _xtime(a1 ^ a2)
                s[i + 2] = a2 ^ x ^ _xtime(a2 ^ a3)
                s[i + 3] = a3 ^ x ^ _xtime(a3 ^ a0)
        rk = rnd << 2
        s = [s[i] ^ w[rk + (i >> 2)][i & 3] for i in range(16)]
    return bytes(s)


def selftest():
    w = expand_key(bytes(range(32)))
    got = encrypt_block(w, bytes.fromhex('00112233445566778899aabbccddeeff'))
    ok = got == bytes.fromhex('8ea2b7ca516745bfeafc49904b496089')
    print('[selftest] %s %s' % (got.hex(), 'OK' if ok else 'FAIL'))
    return ok


# ------------------------------------------------------------ 魔改 CFB 解密
def decrypt_gdc(raw):
    """返回 (明文长度, 原生 .gdc 字节)。明文就是 GDSC + version + zstd 帧。"""
    if len(raw) < 40:
        raise ValueError('too short: %d' % len(raw))
    length = struct.unpack_from('<Q', raw, 16)[0]
    iv = bytearray(raw[24:40])
    lsize = (length + 15) & ~15
    if len(raw) < 40 + lsize:
        raise ValueError('need %d bytes, got %d' % (40 + lsize, len(raw)))
    data = raw[40:40 + lsize]

    w = expand_key(KEY)
    plain = bytearray(length)
    n = 0
    for i in range(length):
        if n == 0:
            iv[:] = encrypt_block(w, bytes(iv))
        c = data[i]
        plain[i] = iv[n] ^ c ^ n
        iv[n] = c ^ n
        n = (n + 1) & 15

    out = bytes(plain)
    if out[:4] != b'GDSC':
        raise ValueError('bad magic %r' % out[:4])
    return length, out


# ------------------------------------------------------------------ 递归
def walk(root, skip):
    for base, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if os.path.join(base, d) != skip]
        for f in files:
            if f.endswith('.gdc'):
                yield os.path.join(base, f)


def main():
    if len(sys.argv) < 2 or sys.argv[1] == '--selftest':
        return 0 if selftest() else 1
    if not selftest():
        print('[!] AES 实现错误，后面结果不可信')
        return 1

    src = sys.argv[1]
    dst = sys.argv[2] if len(sys.argv) > 2 else os.path.join(src, '_decoded')
    ok = bad = 0
    for path in walk(src, dst):
        rel = os.path.relpath(path, src)
        target = os.path.join(dst, rel)
        os.makedirs(os.path.dirname(target), exist_ok=True)
        try:
            with open(path, 'rb') as fp:
                length, out = decrypt_gdc(fp.read())
            with open(target, 'wb') as fp:
                fp.write(out)
            ver = struct.unpack_from('<I', out, 4)[0]
            dsize = struct.unpack_from('<I', out, 8)[0] if len(out) >= 12 else -1
            print('OK   %-42s ver=%-3d %5dB' % (rel, ver, len(out)))
            ok += 1
        except Exception as exc:
            print('FAIL %-42s %s' % (rel, exc))
            bad += 1
    print('\n%d ok, %d fail -> %s' % (ok, bad, dst))
    return 0 if bad == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
