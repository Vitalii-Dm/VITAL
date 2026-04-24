# Wire schema

## CSI UDP frame (ESP32 → backend :5005)

Version 2 (VITAL) — little-endian. See `backend/app/ingest/csi_udp.py` for decoder.

```
offset  size  field
0       1     version (=2)
1       1     node_id
2       2     seq (u16)
4       4     timestamp_ms (u32)
8       2     n_subcarriers (u16)       — typically 56
10      4     temp_c × 100   (i32)       — BME280
14      4     rh_pct × 100   (u32)       — BME280
18      2*n   amplitude[i]  (i16)
18+2n   2*n   phase[i]      (i16)
```

## Dashboard WebSocket (backend → browser `/ws/dashboard`)

One JSON message per zone per fusion tick (~500 ms):

```json
{
  "type": "fusion",
  "zone": "zone-1",
  "severity": "low | medium | high",
  "event": "normal | fall | heat_exhaustion | cardiac | loss_of_consciousness | unknown_medical",
  "label": "Heat exhaustion probable",
  "confidence": 0.82,
  "flagged_layers": ["wifi", "vision", "env"],
  "reasons": ["breathing rapid (45 bpm)", "person on floor 12s", "wet-bulb 31.5°C"],
  "timestamp": 1745337600.123,
  "bpm": 45.0,
  "temp_c": 35.0,
  "rh_pct": 70.0,
  "wetbulb_c": 31.5,
  "waveform": [0.12, -0.08],
  "persons": [
    {
      "track_id": 3,
      "horizontal": true,
      "down_seconds": 12.4,
      "posture": "on_floor",
      "standing": false,
      "keypoints": [[x, y, conf]]
    }
  ],
  "max_down_seconds": 12.4,
  "standing_count": 1,
  "pose_stale": false
}
```

- `persons` — pass-through of the latest pose snapshot (no bbox, no image data).
- `max_down_seconds` — longest on-floor duration across tracked persons, 0 if none.
- `standing_count` — how many tracks are classified as `standing` in the latest
  snapshot. Informational; not fed into severity logic.
- `pose_stale` — true when no pose heartbeat has been received for >3 s.
  Stays false until the first heartbeat arrives.

A `max_down_seconds >= 20` forces `severity = "high"` (pose-only override) and
adds an `"on floor ≥20s"` reason. The backend also emits a one-shot
`EMERGENCY_DISPATCH` log line the first time this fires per zone (debounced
for 60 s). The future ElevenLabs / 911 pipeline subscribes to this.

## Pose ingest WebSocket (pose worker → backend `/ws/ingest/pose`)

Snapshot — one per stride (~100 ms):

```json
{
  "zone": "zone-1",
  "timestamp": 1745337600.123,
  "persons": [
    {
      "track_id": 3,
      "horizontal": true,
      "down_seconds": 12.4,
      "posture": "on_floor",
      "standing": false,
      "bbox": [x1, y1, x2, y2],
      "keypoints": [[x, y, conf]]
    }
  ]
}
```

- `persons` is always present (possibly empty).
- `keypoints` is an array of 17 `[x, y, conf]` entries in COCO order.
- `horizontal` is the derived torso-axis boolean for that person.
- `down_seconds` is the seconds since that tracked identity crossed into
  the "on floor" debounce. 0 when off-floor.
- `posture` is one of `"standing" | "on_floor" | "unknown"`. Debounced over
  3 consecutive frames so zone-level counts don't flicker.
- `standing` is the convenience boolean `posture == "standing"` (dashboard
  uses this rather than string-compare).
- No image data, no face data — only skeletons and bboxes.

Heartbeat — one per ~1 s:

```json
{"type": "heartbeat", "zone": "zone-1", "timestamp": 1745337600.123}
```
