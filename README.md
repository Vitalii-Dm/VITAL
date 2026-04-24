# VITAL

**Invisible guardian for warehouse workers.** WiFi sensing + computer vision + environmental intelligence → one system that detects medical events in under 2 seconds. No wearables. No face recognition. No surveillance.

HackUPC Barcelona · 2026-04-24 · Team of 4 (University of Manchester)

## Architecture

```
ESP32-S3 nodes ──UDP:5005──► FastAPI ingest ──► signal processing ──┐
  (WiFi CSI + BME280)                                               │
                                                                    ▼
laptop webcam ──► YOLOv8-Pose worker ──WebSocket──► fusion engine ──┤
                                                                    │
                      ┌─────────────────────────────────────────────┘
                      ▼
              ┌───────────────┬──────────────┬──────────────────┐
              ▼               ▼              ▼                  ▼
     Next.js dashboard   Worker PWA     Twilio SMS         LED strip
     (supervisor)        (heat nudges)  (HIGH alerts)      (zone status)
```

Three layers:
1. **WiFi CSI** — breathing rate + motion, anonymous by physics
2. **Computer Vision** — YOLOv8-Pose on webcam, keypoints only (no faces)
3. **Environmental** — BME280 wet-bulb temperature for heat-stress context

Fusion: 1 layer flags → log only · 2 layers → supervisor alert · 3 layers → HIGH emergency (SMS + audible alarm).

## Repo layout

- `firmware/esp32-csi-node/` — ESP-IDF project for ESP32-S3 nodes (forked from [ruvnet/RuView](https://github.com/ruvnet/RuView), MIT)
- `backend/` — FastAPI fusion engine, signal processing, alerts
- `backend/pose_worker/` — YOLOv8n-Pose runner (separate process)
- `frontend/` — Next.js 15 supervisor dashboard + worker PWA
- `shared/` — JSON schemas shared between backend and frontend
- `scripts/` — mock data emitters for development without hardware

## Quick start (no hardware required)

You'll drive the system end-to-end with two synthetic data sources that impersonate the WiFi sensor and webcam. Open **four terminals**, all started from the repo root.

### One-time setup

```bash
cp .env.example .env

# backend — creates .venv and installs deps
cd backend
python3 -m venv .venv
.venv/bin/pip install -e .
cd ..

# frontend
cd frontend
npm install
cp .env.local.example .env.local
cd ..
```

### Terminal 1 — backend (the fusion engine)

```bash
cd backend
.venv/bin/uvicorn app.main:app --reload
```

Expect `VITAL backend up` and `CSI UDP listener binding 0.0.0.0:5005`. Leave running.

### Terminal 2 — frontend (supervisor dashboard + worker PWA)

```bash
cd frontend
npm run dev
```

Open http://localhost:3000/dashboard — you'll see an empty floor plan until data starts flowing.

### Terminal 3 — synthetic WiFi CSI (fake ESP32)

```bash
backend/.venv/bin/python scripts/fake_csi.py --scenario breathing-then-collapse
```

Emits 45 s of normal breathing (~16 bpm) at `zone-1`, then the worker's breathing turns rapid, motion stops, and the zone heats up. Within ~10 s you should see a live breathing waveform on the dashboard.

### Terminal 4 — synthetic YOLO pose (fake webcam)

```bash
backend/.venv/bin/python scripts/fake_yolo.py --scenario fall-at-45s
```

Streams "upright" pose events, then "horizontal" at t=45 s. Runs alongside terminal 3 so the fall aligns with the CSI collapse.

### What to watch for

At roughly t=45 s the dashboard should:
- Flash `zone-1` red (pulsing border).
- Display an alert card labelled **HEAT EXHAUSTION PROBABLE — HIGH**.
- Start a response-time counter.
- Log `HIGH alert zone=zone-1 event=heat_exhaustion` in terminal 1.

In parallel, http://localhost:3000/worker shows the same zone's temp / humidity / wet-bulb and live heat-stress advice.

### Other scenarios

```bash
# 2-layer medium: hot zone, no fall
python scripts/fake_csi.py --scenario hot-zone
python scripts/fake_yolo.py --scenario standing

# 1-layer low: fall only, no breathing anomaly, cool zone
python scripts/fake_csi.py --scenario normal
python scripts/fake_yolo.py --scenario fall-at-45s --fall-at 10
```

### Troubleshooting

- **Dashboard stuck on `● DISCONNECTED`** — terminal 1 isn't up, or `NEXT_PUBLIC_BACKEND_WS` in `frontend/.env.local` doesn't match.
- **`npm install` fails on peer deps** — try `npm install --legacy-peer-deps`.
- **BPM stays at 0** — normal for the first ~5 s (algorithm needs a warmup window). If it never comes up, check terminal 1 for UDP errors.
- **`next: command not found` after install** — install silently failed; delete `node_modules` and `package-lock.json` and re-run.

## Hardware setup

See [firmware/esp32-csi-node/README.md](firmware/esp32-csi-node/README.md) for flashing + provisioning.

## Attribution

ESP32 CSI firmware and breathing-extraction algorithm adapted from [ruvnet/RuView](https://github.com/ruvnet/RuView) (MIT).
# VITAL
