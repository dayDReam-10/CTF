import struct

KEY = bytes.fromhex('ce4df8753b59a5a39ade58ac07ef947a3da39f2af75e3284d51217c04d49a061')

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
    w = [list(key[i:i+4]) for i in range(0, 32, 4)]
    rcon = 1
    for i in range(8, 60):
        t = list(w[i-1])
        if i % 8 == 0:
            t = t[1:] + t[:1]
            t = [SBOX[b] for b in t]
            t[0] ^= rcon
            rcon = _xtime(rcon)
        elif i % 8 == 4:
            t = [SBOX[b] for b in t]
        w.append([w[i-8][j] ^ t[j] for j in range(4)])
    return w

def encrypt_block(w, block):
    s = [block[i] ^ w[i>>2][i&3] for i in range(16)]
    for rnd in range(1, 15):
        s = [SBOX[b] for b in s]
        t = [0]*16
        for i in range(16):
            c, r = i>>2, i&3
            t[i] = s[(((c+r)&3)<<2)+r]
        s = t
        if rnd != 14:
            for c in range(4):
                i = c<<2
                a0,a1,a2,a3 = s[i],s[i+1],s[i+2],s[i+3]
                x = a0^a1^a2^a3
                s[i]   = a0^x^_xtime(a0^a1)
                s[i+1] = a1^x^_xtime(a1^a2)
                s[i+2] = a2^x^_xtime(a2^a3)
                s[i+3] = a3^x^_xtime(a3^a0)
        rk = rnd<<2
        s = [s[i] ^ w[rk+(i>>2)][i&3] for i in range(16)]
    return bytes(s)

raw = open('sec2026.gdextension', 'rb').read()
length = struct.unpack_from('<Q', raw, 16)[0]
iv = bytearray(raw[24:40])
lsize = (length + 15) & ~15
data = raw[40:40+lsize]

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

print(plain.decode('utf-8', 'replace'))