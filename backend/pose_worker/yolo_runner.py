"""YOLOv8n-Pose on laptop webcam → fall/horizontal flags → backend WS.

Run with::

    pip install -e .[pose]
    python -m pose_worker.yolo_runner --zone zone-1 --webcam 0

No faces are stored or transmitted. Only skeleton keypoints and derived flags.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import time
from dataclasses import dataclass

log = logging.getLogger("pose_worker")

COCO_NOSE = 0
COCO_L_SHOULDER = 5
COCO_R_SHOULDER = 6
COCO_L_HIP = 11
COCO_R_HIP = 12


@dataclass
class PoseReading:
    horizontal: bool
    fall_transient: bool
    has_person: bool


def classify_pose(keypoints_xy, conf) -> PoseReading:
    """Decide horizontal / fall from a single-person 17-keypoint skeleton.

    Person is 'horizontal' if shoulder-hip axis is closer to horizontal than
    vertical. Confidence-weighted so noisy keypoints don't trigger.
    """
    if keypoints_xy is None or len(keypoints_xy) == 0:
        return PoseReading(False, False, False)

    def pt(i):
        return keypoints_xy[i], float(conf[i]) if conf is not None else 1.0

    (sl, sl_c), (sr, sr_c) = pt(COCO_L_SHOULDER), pt(COCO_R_SHOULDER)
    (hl, hl_c), (hr, hr_c) = pt(COCO_L_HIP), pt(COCO_R_HIP)

    shoulders_c = min(sl_c, sr_c)
    hips_c = min(hl_c, hr_c)
    if shoulders_c < 0.3 or hips_c < 0.3:
        return PoseReading(False, False, False)

    shoulder_y = (sl[1] + sr[1]) / 2
    hip_y = (hl[1] + hr[1]) / 2
    shoulder_x = (sl[0] + sr[0]) / 2
    hip_x = (hl[0] + hr[0]) / 2

    dy = abs(shoulder_y - hip_y)
    dx = abs(shoulder_x - hip_x)
    horizontal = dx > dy * 1.3  # torso axis more horizontal than vertical
    return PoseReading(horizontal=horizontal, fall_transient=False, has_person=True)


async def _send(ws, msg: dict) -> None:
    await ws.send(json.dumps(msg))


async def run(zone: str, webcam: int, backend_ws: str, model_path: str, stride_ms: int) -> None:
    import cv2
    import websockets
    from ultralytics import YOLO

    log.info("loading YOLO model %s …", model_path)
    model = YOLO(model_path)
    cap = cv2.VideoCapture(webcam)
    if not cap.isOpened():
        raise SystemExit(f"cannot open webcam index {webcam}")

    prev_horizontal = False
    last_standing_t = time.time()
    stride_s = stride_ms / 1000.0

    log.info("connecting to %s …", backend_ws)
    async with websockets.connect(backend_ws) as ws:
        while True:
            ok, frame = cap.read()
            if not ok:
                await asyncio.sleep(0.05)
                continue

            results = model.predict(frame, verbose=False, conf=0.4)
            reading = PoseReading(False, False, False)
            if results and results[0].keypoints is not None and len(results[0].keypoints) > 0:
                kp = results[0].keypoints[0]
                xy = kp.xy[0].cpu().numpy() if kp.xy is not None else None
                conf = kp.conf[0].cpu().numpy() if kp.conf is not None else None
                reading = classify_pose(xy, conf)

            # Fall transient: was standing <2s ago, now horizontal.
            now = time.time()
            if not reading.horizontal:
                last_standing_t = now
            fall_transient = reading.horizontal and (now - last_standing_t) < 2.0 and not prev_horizontal
            prev_horizontal = reading.horizontal

            await _send(
                ws,
                {
                    "zone": zone,
                    "horizontal": reading.horizontal,
                    "fall_transient": fall_transient,
                    "has_person": reading.has_person,
                },
            )
            await asyncio.sleep(stride_s)


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
    parser.add_argument("--stride-ms", type=int, default=100)
    args = parser.parse_args()

    asyncio.run(run(args.zone, args.webcam, args.backend_ws, args.model, args.stride_ms))


if __name__ == "__main__":
    main()
