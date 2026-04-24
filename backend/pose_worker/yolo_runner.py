"""YOLOv8n-Pose on laptop webcam → multi-person on-floor timer → backend WS.

Run with::

    pip install -e .[pose]
    python -m pose_worker.yolo_runner --zone zone-1 --webcam 0

No faces are stored or transmitted. Only skeleton keypoints (17 per person),
bounding boxes, and derived flags.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import time
from collections import deque
from dataclasses import dataclass, field

log = logging.getLogger("pose_worker")

COCO_L_SHOULDER = 5
COCO_R_SHOULDER = 6
COCO_L_HIP = 11
COCO_R_HIP = 12

# Defaults — CLI overridable.
DEFAULT_STRIDE_MS = 100
DEFAULT_DEBOUNCE_ENTER = 5
DEFAULT_DEBOUNCE_EXIT = 5
# Standing is less consequential than on_floor — 3 frames is enough to
# keep counts from flickering without adding obvious lag.
DEFAULT_DEBOUNCE_POSTURE = 3
DEFAULT_ASPECT_RATIO_THRESHOLD = 1.2
DEFAULT_LOW_VELOCITY_PX = 3.0  # mean per-keypoint L2 motion over ~1 s
DEFAULT_TRACK_TTL_S = 3.0      # drop tracks not seen for this long
HEARTBEAT_S = 1.0

POSTURE_STANDING = "standing"
POSTURE_ON_FLOOR = "on_floor"
POSTURE_UNKNOWN = "unknown"


@dataclass
class _TrackState:
    # rolling window of (timestamp, keypoints_xy_array) for velocity estimate
    kp_history: deque = field(default_factory=lambda: deque(maxlen=20))
    on_floor_streak: int = 0
    off_floor_streak: int = 0
    down_since: float | None = None
    last_seen: float = 0.0
    # Posture debounce — separate from the on_floor timer because we commit
    # a label only after a short streak to avoid flickering standing counts.
    posture: str = POSTURE_UNKNOWN
    candidate_posture: str = POSTURE_UNKNOWN
    posture_streak: int = 0


def _torso_horizontal(xy, conf) -> bool:
    """Old rule: shoulder-hip axis more horizontal than vertical."""
    if xy is None or len(xy) < 13 or conf is None:
        return False
    try:
        sl, sr = xy[COCO_L_SHOULDER], xy[COCO_R_SHOULDER]
        hl, hr = xy[COCO_L_HIP], xy[COCO_R_HIP]
        sl_c, sr_c = float(conf[COCO_L_SHOULDER]), float(conf[COCO_R_SHOULDER])
        hl_c, hr_c = float(conf[COCO_L_HIP]), float(conf[COCO_R_HIP])
    except (IndexError, TypeError):
        return False

    if min(sl_c, sr_c) < 0.3 or min(hl_c, hr_c) < 0.3:
        return False

    shoulder_y = (sl[1] + sr[1]) / 2
    hip_y = (hl[1] + hr[1]) / 2
    shoulder_x = (sl[0] + sr[0]) / 2
    hip_x = (hl[0] + hr[0]) / 2

    dy = abs(shoulder_y - hip_y)
    dx = abs(shoulder_x - hip_x)
    return dx > dy * 1.3


def _aspect_ratio(bbox) -> float:
    x1, y1, x2, y2 = bbox
    w = max(1e-6, float(x2 - x1))
    h = max(1e-6, float(y2 - y1))
    return w / h


def _bbox_hw_ratio(bbox) -> float:
    """Height-over-width. Inverse of `_aspect_ratio` — useful for upright check."""
    x1, y1, x2, y2 = bbox
    w = max(1e-6, float(x2 - x1))
    h = max(1e-6, float(y2 - y1))
    return h / w


def _torso_vertical(xy, conf) -> bool:
    """Shoulder-hip axis more vertical than horizontal, hips below shoulders.

    Mirror of `_torso_horizontal`: requires the same ≥0.3 keypoint confidence
    but enforces dy > dx and a meaningful positive dy (hips below shoulders
    in image coordinates — y grows downward).
    """
    if xy is None or len(xy) < 13 or conf is None:
        return False
    try:
        sl, sr = xy[COCO_L_SHOULDER], xy[COCO_R_SHOULDER]
        hl, hr = xy[COCO_L_HIP], xy[COCO_R_HIP]
        sl_c, sr_c = float(conf[COCO_L_SHOULDER]), float(conf[COCO_R_SHOULDER])
        hl_c, hr_c = float(conf[COCO_L_HIP]), float(conf[COCO_R_HIP])
    except (IndexError, TypeError):
        return False

    if min(sl_c, sr_c) < 0.3 or min(hl_c, hr_c) < 0.3:
        return False

    shoulder_y = (sl[1] + sr[1]) / 2
    hip_y = (hl[1] + hr[1]) / 2
    shoulder_x = (sl[0] + sr[0]) / 2
    hip_x = (hl[0] + hr[0]) / 2

    dy = float(hip_y - shoulder_y)   # signed: positive when hips below shoulders
    dx = float(abs(shoulder_x - hip_x))
    # A "meaningful" dy — filter out cases where the person is too small /
    # the hip-shoulder distance is near zero to be informative.
    if dy <= 0 or dy < 20:
        return False
    return dy > dx


def _classify_posture(
    xy, conf, bbox, on_floor: bool, aspect_threshold: float
) -> str:
    """One of POSTURE_STANDING / POSTURE_ON_FLOOR / POSTURE_UNKNOWN.

    `on_floor` is the already-computed debounced-input from `_is_on_floor`.
    Standing requires vertical torso AND tall bbox (h/w > threshold). Anything
    ambiguous falls back to unknown so the dashboard can grey it out.
    """
    if on_floor:
        return POSTURE_ON_FLOOR
    vertical = _torso_vertical(xy, conf)
    tall = _bbox_hw_ratio(bbox) > aspect_threshold
    if vertical and tall:
        return POSTURE_STANDING
    return POSTURE_UNKNOWN


def _mean_velocity(history: deque, now: float, window_s: float = 1.0) -> float:
    """Mean L2 displacement per keypoint over the last ~window_s seconds."""
    recent = [(t, kp) for (t, kp) in history if (now - t) <= window_s]
    if len(recent) < 2:
        return float("inf")  # not enough data → don't count as "low velocity"
    import numpy as np

    kp0 = recent[0][1]
    kp1 = recent[-1][1]
    if kp0 is None or kp1 is None or kp0.shape != kp1.shape:
        return float("inf")
    dx = kp1[:, 0] - kp0[:, 0]
    dy = kp1[:, 1] - kp0[:, 1]
    dist = np.sqrt(dx * dx + dy * dy)
    return float(np.mean(dist))


def _is_on_floor(
    torso_h: bool, aspect_ratio: float, mean_vel: float,
    aspect_threshold: float, vel_threshold: float,
) -> bool:
    # Any strong cue wins. Torso axis alone is the conservative original rule.
    # Aspect ratio + low velocity backs it up for cases where the torso
    # keypoints are occluded (e.g. face-down).
    if torso_h:
        return True
    if aspect_ratio > aspect_threshold and mean_vel < vel_threshold:
        return True
    return False


async def _send(ws, msg: dict) -> None:
    await ws.send(json.dumps(msg))


async def _run_once(
    ws,
    zone: str,
    cap,
    model,
    *,
    stride_s: float,
    debounce_enter: int,
    debounce_exit: int,
    debounce_posture: int,
    aspect_threshold: float,
    vel_threshold: float,
    track_ttl_s: float,
) -> None:
    import numpy as np

    tracks: dict[int, _TrackState] = {}
    last_heartbeat = 0.0

    while True:
        ok, frame = cap.read()
        if not ok:
            await asyncio.sleep(0.05)
            continue

        now = time.time()
        # model.track preserves identities across frames via ByteTrack.
        results = model.track(
            frame, persist=True, tracker="bytetrack.yaml", verbose=False, conf=0.4
        )

        persons_out: list[dict] = []
        seen_ids: set[int] = set()

        if results and len(results) > 0:
            r0 = results[0]
            kps = r0.keypoints
            boxes = r0.boxes
            if kps is not None and boxes is not None and len(boxes) > 0:
                xy_all = kps.xy.cpu().numpy() if kps.xy is not None else None
                conf_all = kps.conf.cpu().numpy() if kps.conf is not None else None
                xyxy_all = boxes.xyxy.cpu().numpy() if boxes.xyxy is not None else None
                ids = boxes.id
                ids_np = ids.cpu().numpy().astype(int) if ids is not None else None

                for i in range(len(boxes)):
                    track_id = int(ids_np[i]) if ids_np is not None else i
                    seen_ids.add(track_id)
                    xy = xy_all[i] if xy_all is not None else None
                    cf = conf_all[i] if conf_all is not None else None
                    bbox = xyxy_all[i].tolist() if xyxy_all is not None else [0, 0, 0, 0]

                    st = tracks.setdefault(track_id, _TrackState())
                    if xy is not None:
                        st.kp_history.append((now, np.asarray(xy, dtype=float)))
                    st.last_seen = now

                    torso_h = _torso_horizontal(xy, cf)
                    ar = _aspect_ratio(bbox)
                    vel = _mean_velocity(st.kp_history, now)
                    on_floor = _is_on_floor(
                        torso_h, ar, vel, aspect_threshold, vel_threshold
                    )

                    if on_floor:
                        st.on_floor_streak += 1
                        st.off_floor_streak = 0
                        if st.down_since is None and st.on_floor_streak >= debounce_enter:
                            st.down_since = now
                    else:
                        st.off_floor_streak += 1
                        st.on_floor_streak = 0
                        if st.down_since is not None and st.off_floor_streak >= debounce_exit:
                            st.down_since = None

                    down_seconds = (now - st.down_since) if st.down_since is not None else 0.0

                    # Debounced posture label. We use the already-debounced
                    # on_floor signal (via down_since) so "on_floor" here
                    # agrees with the timer. Standing/unknown need their own
                    # small streak filter to stop counts flickering.
                    raw_posture = _classify_posture(
                        xy, cf, bbox,
                        on_floor=(st.down_since is not None),
                        aspect_threshold=aspect_threshold,
                    )
                    if raw_posture == st.candidate_posture:
                        st.posture_streak += 1
                    else:
                        st.candidate_posture = raw_posture
                        st.posture_streak = 1
                    if st.posture_streak >= debounce_posture:
                        st.posture = raw_posture
                    # else: keep previous committed posture (sticky)

                    # Keypoints shaped as [[x, y, conf], ... 17].
                    kp_out: list[list[float]] = []
                    if xy is not None and cf is not None and len(xy) >= 17:
                        for j in range(17):
                            kp_out.append(
                                [float(xy[j][0]), float(xy[j][1]), float(cf[j])]
                            )
                    else:
                        kp_out = [[0.0, 0.0, 0.0] for _ in range(17)]

                    persons_out.append(
                        {
                            "track_id": track_id,
                            "horizontal": bool(torso_h),
                            "down_seconds": float(down_seconds),
                            "posture": st.posture,
                            "standing": st.posture == POSTURE_STANDING,
                            "bbox": [float(v) for v in bbox],
                            "keypoints": kp_out,
                        }
                    )

        # Drop stale tracks.
        for tid in list(tracks.keys()):
            if (now - tracks[tid].last_seen) > track_ttl_s:
                tracks.pop(tid, None)

        await _send(
            ws,
            {"zone": zone, "timestamp": now, "persons": persons_out},
        )

        if (now - last_heartbeat) >= HEARTBEAT_S:
            await _send(
                ws,
                {"type": "heartbeat", "zone": zone, "timestamp": now},
            )
            last_heartbeat = now

        await asyncio.sleep(stride_s)


async def run(
    zone: str,
    webcam: int,
    backend_ws: str,
    model_path: str,
    stride_ms: int,
    debounce_enter: int,
    debounce_exit: int,
    debounce_posture: int,
    aspect_threshold: float,
    vel_threshold: float,
    track_ttl_s: float,
) -> None:
    import cv2
    import websockets
    from ultralytics import YOLO

    log.info("loading YOLO model %s …", model_path)
    model = YOLO(model_path)
    cap = cv2.VideoCapture(webcam)
    if not cap.isOpened():
        raise SystemExit(f"cannot open webcam index {webcam}")

    stride_s = stride_ms / 1000.0

    backoff = 1.0
    while True:
        try:
            log.info("connecting to %s …", backend_ws)
            async with websockets.connect(backend_ws) as ws:
                log.info("connected; starting capture loop")
                backoff = 1.0  # reset on successful connect
                await _run_once(
                    ws,
                    zone,
                    cap,
                    model,
                    stride_s=stride_s,
                    debounce_enter=debounce_enter,
                    debounce_exit=debounce_exit,
                    debounce_posture=debounce_posture,
                    aspect_threshold=aspect_threshold,
                    vel_threshold=vel_threshold,
                    track_ttl_s=track_ttl_s,
                )
        except (OSError, ConnectionError) as e:
            log.warning("backend ws connect/recv failed: %s; retrying in %.1fs", e, backoff)
        except Exception as e:  # noqa: BLE001 — we want to survive any transient fault
            log.exception("pose worker loop crashed: %s; retrying in %.1fs", e, backoff)
        await asyncio.sleep(backoff)
        backoff = min(30.0, backoff * 2.0)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    parser = argparse.ArgumentParser()
    parser.add_argument("--zone", default="zone-1")
    parser.add_argument("--webcam", type=int, default=int(os.getenv("YOLO_WEBCAM_INDEX", "0")))
    parser.add_argument(
        "--backend-ws",
        default=os.getenv("YOLO_BACKEND_WS", "ws://localhost:8000/ws/ingest/pose"),
    )
    parser.add_argument("--model", default=os.getenv("YOLO_MODEL", "yolov8n-pose.pt"))
    parser.add_argument("--stride-ms", type=int, default=DEFAULT_STRIDE_MS)
    parser.add_argument("--debounce-enter", type=int, default=DEFAULT_DEBOUNCE_ENTER)
    parser.add_argument("--debounce-exit", type=int, default=DEFAULT_DEBOUNCE_EXIT)
    parser.add_argument(
        "--debounce-posture", type=int, default=DEFAULT_DEBOUNCE_POSTURE
    )
    parser.add_argument(
        "--aspect-threshold", type=float, default=DEFAULT_ASPECT_RATIO_THRESHOLD
    )
    parser.add_argument(
        "--vel-threshold", type=float, default=DEFAULT_LOW_VELOCITY_PX
    )
    parser.add_argument("--track-ttl-s", type=float, default=DEFAULT_TRACK_TTL_S)
    args = parser.parse_args()

    asyncio.run(
        run(
            args.zone,
            args.webcam,
            args.backend_ws,
            args.model,
            args.stride_ms,
            args.debounce_enter,
            args.debounce_exit,
            args.debounce_posture,
            args.aspect_threshold,
            args.vel_threshold,
            args.track_ttl_s,
        )
    )


if __name__ == "__main__":
    main()
