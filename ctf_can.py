"""Shared python-can helpers for the three post-event CHV CTF solvers."""

from __future__ import annotations

import time
import can

DTC_TX_ID = 0x7E0
DTC_RX_ID = 0x7E8
CSHIM_TX_ID = 0x666
CSHIM_RX_ID = 0x66E


def open_bus(interface: str, backend: str, bitrate: int = 500_000):
    if backend == "auto":
        backend = "chv" if interface.startswith("/dev/") or interface == "auto" else "socketcan"
    try:
        return can.Bus(interface=backend, channel=interface, bitrate=bitrate)
    except can.CanInterfaceNotImplementedError as exc:
        if backend == "chv":
            raise SystemExit(
                "The external chv-badgetools python-can plugin is required for USB/SLCAN. "
                "Install it separately from its official repository."
            ) from exc
        raise


def show(direction: str, arbitration_id: int, data: bytes, fd: bool = False):
    marker = " FD" if fd else ""
    print(f"{direction} {arbitration_id:08X} [{len(data):2d}] {data.hex(' ').upper()}{marker}")


def send(bus, arbitration_id: int, data: bytes, fd: bool = False):
    show("TX", arbitration_id, data, fd)
    bus.send(can.Message(
        arbitration_id=arbitration_id,
        data=data,
        is_extended_id=arbitration_id > 0x7FF,
        is_fd=fd,
        bitrate_switch=fd,
    ))


def recv_id(bus, arbitration_id: int, timeout: float) -> bytes:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        message = bus.recv(max(0, deadline - time.monotonic()))
        if message is None:
            break
        data = bytes(message.data)
        show("RX", message.arbitration_id, data, message.is_fd)
        if message.arbitration_id == arbitration_id:
            return data
    raise TimeoutError(f"response timeout for CAN ID 0x{arbitration_id:X}")


def send_uds(bus, payload: bytes):
    fd = len(payload) > 8
    send(bus, DTC_TX_ID, payload, fd)


def receive_uds(bus, timeout: float) -> bytes:
    deadline = time.monotonic() + timeout
    chunks = []
    total = None
    while time.monotonic() < deadline:
        message = bus.recv(max(0, deadline - time.monotonic()))
        if message is None:
            break
        data = bytes(message.data)
        show("RX", message.arbitration_id, data, message.is_fd)
        if message.arbitration_id != DTC_RX_ID or not data:
            continue

        # CAN-FD ISO-TP extended single frame: 00 length payload...
        if len(data) >= 2 and data[0] == 0 and data[1] <= len(data) - 2:
            return data[2:2 + data[1]]

        # Classical ISO-TP first/consecutive frames, retained for compatibility.
        if data[0] >> 4 == 1 and len(data) >= 2:
            total = ((data[0] & 0x0F) << 8) | data[1]
            chunks = [data[2:]]
            continue
        if total is not None and data[0] >> 4 == 2:
            chunks.append(data[1:])
            payload = b"".join(chunks)[:total]
            if len(payload) >= total:
                return payload
            continue
        return data
    raise TimeoutError("UDS response timeout")


def exchange(bus, payload: bytes, timeout: float, dry_run: bool = False, fd: bool = False) -> bytes:
    show("TX", CSHIM_TX_ID, payload, fd)
    if dry_run:
        return b""
    bus.send(can.Message(
        arbitration_id=CSHIM_TX_ID,
        data=payload,
        is_extended_id=False,
        is_fd=fd,
        bitrate_switch=fd,
    ))
    return recv_id(bus, CSHIM_RX_ID, timeout)
