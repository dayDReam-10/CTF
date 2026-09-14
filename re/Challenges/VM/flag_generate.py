#!/usr/bin/env python3
"""Generate the expected RC4 bytes for the VM challenge."""

import argparse


MASK32 = 0xFFFFFFFF


def transform(data: bytes, add: int, sub: int, mul: int, xor: int, rotate: int) -> bytearray:
    result = bytearray(data)
    for index, value in enumerate(result):
        value = ((value + add - sub) * mul) & MASK32
        value ^= xor
        rotate %= 32
        value = ((value << rotate) | (value >> (32 - rotate))) & MASK32
        result[index] = value & 0xFF
    return result


def rc4(data: bytearray, key: bytes) -> bytearray:
    state = list(range(256))
    j = 0
    for index in range(256):
        j = (j + state[index] + key[index % len(key)]) & 0xFF
        state[index], state[j] = state[j], state[index]

    i = 0
    j = 0
    for index in range(len(data)):
        i = (i + 1) & 0xFF
        j = (j + state[i]) & 0xFF
        state[i], state[j] = state[j], state[i]
        stream = state[(state[i] + state[j]) & 0xFF]
        data[index] ^= stream
    return data


def generate(flag: str, key: bytes, add: int, sub: int, mul: int,
             xor: int, rotate: int) -> bytes:
    return bytes(rc4(transform(flag.encode("ascii"), add, sub, mul, xor, rotate), key))


def format_c_array(data: bytes, name: str = "expected") -> str:
    lines = [f"static const uint8_t {name}[] = {{"]
    for offset in range(0, len(data), 8):
        chunk = data[offset : offset + 8]
        values = ", ".join(f"0x{value:02X}" for value in chunk)
        lines.append(f"    {values},")
    lines.append("};")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("flag", help="ASCII flag or input string")
    parser.add_argument("--key", default="stackvm", help="RC4 key")
    parser.add_argument("--add", type=int, default=114)
    parser.add_argument("--sub", type=int, default=514)
    parser.add_argument("--mul", type=int, default=19)
    parser.add_argument("--xor", type=int, default=19)
    parser.add_argument("--rol", type=int, default=2)
    parser.add_argument("--name", default="expected", help="C array name")
    args = parser.parse_args()

    try:
        args.flag.encode("ascii")
        key = args.key.encode("ascii")
    except UnicodeEncodeError as error:
        parser.error(f"flag and key must contain ASCII characters: {error}")

    if not key:
        parser.error("RC4 key must not be empty")
    if not 0 <= args.rol < 32:
        parser.error("--rol must be between 0 and 31")

    result = generate(args.flag, key, args.add, args.sub, args.mul, args.xor, args.rol)
    print(f"flag length: {len(args.flag)}")
    print(f"expected RC4 bytes: {result}")
    print(format_c_array(result, args.name))


if __name__ == "__main__":
    main()
