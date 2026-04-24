"""UDP listener for CSI frames streamed from ESP32-S3 nodes.

Frame format (extended from RuView ADR-018 to piggy-back BME280 readings):

    offset  size  field
    0       1     version (=2, VITAL extension)
    1       1     node_id / zone index
    2       2     seq (u16 LE)
    4       4     timestamp_ms (u32 LE, boot-relative)
    8       2     n_subcarriers (u16 LE)
    10      4     temp_c_x100  (i32 LE)  — BME280 temperature × 100
    14      4     rh_pct_x100  (u32 LE)  — BME280 relative humidity × 100
    18      ...   amplitude[i] (i16 LE) for i in 0..n_subcarriers
            ...   phase[i]     (i16 LE) for i in 0..n_subcarriers

Fallback for vanilla RuView frames (version=1) also decoded below.
"""
from __future__ import annotations

import asyncio
import logging
import socket
import struct
from dataclasses import dataclass

import numpy as np

log = logging.getLogger(__name__)


@dataclass
class CsiFrame:
    version: int
    node_id: int
    seq: int
    timestamp_ms: int
    amplitude: np.ndarray  # float32, shape [n]
    phase: np.ndarray      # float32, shape [n]
    temp_c: float | None = None
    rh_pct: float | None = None


def decode(packet: bytes) -> CsiFrame | None:
    if len(packet) < 8:
        return None
    version = packet[0]
    if version == 2:
        if len(packet) < 18:
            return None
        node_id, seq, timestamp_ms, n_sub, temp_x100, rh_x100 = struct.unpack_from(
            "<BHIHiI", packet, 1
        )
        off = 18
        expected = off + n_sub * 4
        if len(packet) < expected:
            return None
        amp = np.frombuffer(packet, dtype="<i2", count=n_sub, offset=off).astype(np.float32)
        phase = np.frombuffer(
            packet, dtype="<i2", count=n_sub, offset=off + n_sub * 2
        ).astype(np.float32)
        return CsiFrame(
            version=2,
            node_id=node_id,
            seq=seq,
            timestamp_ms=timestamp_ms,
            amplitude=amp,
            phase=phase,
            temp_c=temp_x100 / 100.0,
            rh_pct=rh_x100 / 100.0,
        )

    # version 1 — RuView ADR-018 (no env payload)
    if version == 1:
        node_id = packet[1]
        seq = struct.unpack_from("<H", packet, 2)[0]
        timestamp_ms = struct.unpack_from("<I", packet, 4)[0]
        n_sub = struct.unpack_from("<H", packet, 8)[0]
        off = 10
        amp = np.frombuffer(packet, dtype="<i2", count=n_sub, offset=off).astype(np.float32)
        phase = np.frombuffer(
            packet, dtype="<i2", count=n_sub, offset=off + n_sub * 2
        ).astype(np.float32)
        return CsiFrame(
            version=1,
            node_id=node_id,
            seq=seq,
            timestamp_ms=timestamp_ms,
            amplitude=amp,
            phase=phase,
        )

    return None


class _CsiProtocol(asyncio.DatagramProtocol):
    """Decodes each UDP datagram and forwards to the frame handler.

    The handler receives `(frame, source_ip)`. The IP is used to learn a
    zone↔node address mapping so the backend can later send LED colour
    commands back to the right ESP32.
    """

    def __init__(self, on_frame):
        self._on_frame = on_frame

    def datagram_received(self, data: bytes, addr) -> None:
        frame = decode(data)
        if frame is not None:
            source_ip = addr[0] if addr else None
            self._on_frame(frame, source_ip)


async def run_udp_listener(host: str, port: int, on_frame) -> asyncio.DatagramTransport:
    loop = asyncio.get_running_loop()
    log.info("CSI UDP listener binding %s:%d", host, port)
    transport, _ = await loop.create_datagram_endpoint(
        lambda: _CsiProtocol(on_frame),
        local_addr=(host, port),
        family=socket.AF_INET,
    )
    return transport
