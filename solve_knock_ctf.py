#!/usr/bin/env python3
# Copyright © 2026 00One, Inc.
# SPDX-License-Identifier: Apache-2.0

"""Solve the real CTF Speakeasy using the recovered MPY transform."""

import argparse
import time

from ctf_can import open_bus, recv_id, send

INIT_ID = 0x0005EED
TOKEN_ID = 0x0005EEE
KNOCK_ID = 0x0ACCE55
FEEDBACK_ID = 0x0005EF0


def nibble_swap(value):
    return ((value & 0x0F) << 4) | ((value & 0xF0) >> 4)


def timings(token):
    b1, b2, b3 = token[:3]
    return (
        100 + 4 * nibble_swap(b1),
        150 + 3 * (b2 ^ nibble_swap(b3)),
        80 + 2 * nibble_swap(b1 ^ b2),
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("interface", nargs="?", default="can0")
    parser.add_argument("--backend", choices=("auto", "socketcan", "chv"), default="auto")
    parser.add_argument("--timeout", type=float, default=3.0)
    parser.add_argument("--advance-ms", type=int, default=10,
                        help="send each knock this many ms early to absorb USB scheduling jitter")
    args = parser.parse_args()

    bus = open_bus(args.interface, args.backend, 500000)
    try:
        send(bus, INIT_ID, b"\x00")
        token = recv_id(bus, TOKEN_ID, args.timeout)[:4]
        delays = timings(token)
        print(f"token={token.hex()} timings_ms={delays}")
        previous = time.monotonic()
        for index, delay_ms in enumerate(delays, 1):
            target = previous + max(0, delay_ms - args.advance_ms) / 1000
            time.sleep(max(0, target - time.monotonic()))
            send(bus, KNOCK_ID, bytes([index]))
            previous = time.monotonic()
            deadline = time.monotonic() + args.timeout
            while time.monotonic() < deadline:
                message = bus.recv(max(0, deadline - time.monotonic()))
                if message is None:
                    break
                data = bytes(message.data)
                print(f"RX {message.arbitration_id:08X} [{len(data):2d}] {data.hex(' ').upper()}")
                if message.arbitration_id == 0x7FF and b"flag{" in data:
                    flag = data[data.index(b"flag{"):].rstrip(b"\x00")
                    print("FLAG:", flag.decode("ascii", "replace"))
                    return
                if message.arbitration_id == FEEDBACK_ID:
                    if data[:1] != b"\x00":
                        raise RuntimeError(f"knock {index} rejected: {data.hex()}")
                    break

        deadline = time.monotonic() + args.timeout
        while time.monotonic() < deadline:
            message = bus.recv(max(0, deadline - time.monotonic()))
            if message is None:
                break
            data = bytes(message.data)
            print(f"RX {message.arbitration_id:08X} [{len(data):2d}] {data.hex(' ').upper()}")
            start = data.find(b"flag{")
            if start >= 0:
                print("FLAG:", data[start:].rstrip(b"\x00").decode("ascii", "replace"))
    finally:
        try:
            bus.shutdown()
        except Exception:
            pass


if __name__ == "__main__":
    main()
