#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""recover_proj.py — 把 CTF apk 的 assets 解出来、解密、摆成 GDRE 认的工程目录

    python recover_proj.py <apk 或 zip> <输出目录>

之后跑:
    gdre_tools.exe --headless --recover=<输出目录> --bytecode=4.5.0-stable
"""
import io
import os
import struct
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gdc_decrypt import KEY, expand_key, encrypt_block

W = expand_key(KEY)

PROJECT_GODOT = """config_version=5

[application]

config/name="sec2026"
config/features=PackedStringArray("4.5", "Forward Plus")

[rendering]

renderer/rendering_method="forward_plus"
"""


def decrypt(raw):
    """魔改 CFB: m[j] = C[j]^j ; P[j] = m[j]^KS[j] ; feedback = m"""
    length = struct.unpack_from('<Q', raw, 16)[0]
    iv = bytearray(raw[24:40])
    lsize = (length + 15) & ~15
    if len(raw) < 40 + lsize:
        raise ValueError('short: need %d got %d' % (40 + lsize, len(raw)))
    data = raw[40:40 + lsize]
    out = bytearray(length)
    n = 0
    for i in range(length):
        if n == 0:
            iv[:] = encrypt_block(W, bytes(iv))
        c = data[i]
        out[i] = iv[n] ^ c ^ n
        iv[n] = c ^ n
        n = (n + 1) & 15
    return bytes(out)


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 1
    src, proj = sys.argv[1], sys.argv[2]

    z = zipfile.ZipFile(src)
    names = z.namelist()
    if names == ['preliminary.apk'] or names[0].endswith('.apk'):
        inner = zipfile.ZipFile(io.BytesIO(z.read(names[0])))
    else:
        inner = z

    total = ok = fail = 0
    for n in inner.namelist():
        if not n.startswith('assets/'):
            continue
        rel = n[len('assets/'):]
        if not rel:
            continue
        p = os.path.join(proj, rel.replace('/', os.sep))
        os.makedirs(os.path.dirname(p), exist_ok=True)
        b = inner.read(n)
        total += 1
        if n.endswith(('.gdc', '.scn', '.res')):
            try:
                b = decrypt(b)
                ok += 1
            except Exception as exc:
                print('[!] decrypt failed %-40s %s' % (rel, exc))
                fail += 1
        with open(p, 'wb') as fp:
            fp.write(b)

    with open(os.path.join(proj, 'project.godot'), 'w', encoding='utf-8') as fp:
        fp.write(PROJECT_GODOT)

    print('assets=%d decrypted=%d failed=%d -> %s' % (total, ok, fail, proj))
    return 0


if __name__ == '__main__':
    sys.exit(main())
