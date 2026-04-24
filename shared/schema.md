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
  "reasons": ["breathing rapid (45 bpm)", "person horizontal", "wet-bulb 31.5°C"],
  "timestamp": 1745337600.123,
  "bpm": 45.0,
  "temp_c": 35.0,
  "rh_pct": 70.0,
  "wetbulb_c": 31.5,
  "waveform": [0.12, -0.08, ...]
}
```

## Pose ingest WebSocket (pose worker → backend `/ws/ingest/pose`)

```json
{"zone": "zone-1", "horizontal": true, "fall_transient": true, "has_person": true}
```
