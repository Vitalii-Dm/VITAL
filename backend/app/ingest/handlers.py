"""Side-effect-light handlers that update the world state when data arrives.

The CSI UDP listener and the pose WebSocket both call into this module.
Keeping them here (instead of inside the transport layer) means unit tests
can drive the pipeline by calling these functions directly, with no
sockets in the loop.
"""
from __future__ import annotations

import logging
import time

from app.alerts.led_strip import register_address
from app.ingest.csi_udp import CsiFrame
from app.state import world

log = logging.getLogger(__name__)


def on_csi_frame(frame: CsiFrame, source_ip: str | None = None) -> None:
    zone_id = f"zone-{frame.node_id}"
    zone = world.zone(zone_id)
    zone.breathing.push(frame.amplitude)
    zone.last_motion = zone.motion.push(frame.amplitude)
    zone.updated_at = time.time()

    est = zone.breathing.estimate()
    if est is not None:
        zone.last_bpm = est.bpm
        zone.waveform.append(float(frame.amplitude[est.subcarrier_idx]))

    if frame.temp_c is not None:
        zone.last_temp_c = frame.temp_c
    if frame.rh_pct is not None:
        zone.last_rh_pct = frame.rh_pct

    if source_ip is not None:
        register_address(zone_id, source_ip)


def on_vision_event(
    zone_id: str, horizontal: bool, fall_transient: bool
) -> None:
    zone = world.zone(zone_id)
    zone.last_vision_horizontal = horizontal
    zone.last_vision_fall = fall_transient
    zone.updated_at = time.time()
