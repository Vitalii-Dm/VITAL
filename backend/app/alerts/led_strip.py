"""Send WS2812 LED color commands to ESP32 nodes over UDP.

Protocol (VITAL-local, not from RuView): 4 bytes to the node's UDP port 5006.

    offset  size  field
    0       1     version (=1)
    1       1     R
    2       1     G
    3       1     B

If the node's address isn't known yet, this is a no-op — the real ESP32
registers its IP the first time it sends a CSI frame (see future work in
`firmware/esp32-csi-node/VITAL_MODIFICATIONS.md`). For the hackathon demo,
we resolve zones to addresses from a static registry below.
"""
from __future__ import annotations

import logging
import socket
from typing import Final

log = logging.getLogger(__name__)

LED_UDP_PORT: Final[int] = 5006
_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# zone_id → last known sender IP (populated by the CSI UDP listener).
# For the pure-mock demo this can stay empty; LED writes become no-ops.
ZONE_ADDRESSES: dict[str, str] = {}


GREEN = (0, 180, 0)
AMBER = (220, 140, 0)
RED = (220, 0, 0)


def _frame(r: int, g: int, b: int) -> bytes:
    return bytes([1, r & 0xFF, g & 0xFF, b & 0xFF])


def set_zone_color(zone_id: str, rgb: tuple[int, int, int]) -> None:
    addr = ZONE_ADDRESSES.get(zone_id)
    if addr is None:
        log.debug("[led-noop] zone=%s has no registered address", zone_id)
        return
    try:
        _sock.sendto(_frame(*rgb), (addr, LED_UDP_PORT))
    except OSError as e:
        log.warning("LED send failed to %s: %s", addr, e)


def register_address(zone_id: str, ip: str) -> None:
    if ZONE_ADDRESSES.get(zone_id) != ip:
        log.info("zone %s registered at %s", zone_id, ip)
    ZONE_ADDRESSES[zone_id] = ip
