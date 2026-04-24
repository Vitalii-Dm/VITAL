# VITAL firmware modifications (from upstream RuView)

This directory is a fork of [ruvnet/RuView's `firmware/esp32-csi-node/`](https://github.com/ruvnet/RuView), MIT-licensed — see `LICENSE.upstream`. The unmodified upstream already produces a working ESP32-S3 CSI streamer on UDP :5005 with the ADR-018 binary frame format.

For VITAL we need two additions and one extension:

## 1. BME280 I²C reader

**Why:** the fusion engine needs temperature + humidity per zone for wet-bulb calculation.

**Wiring** (BME280 → ESP32-S3 DevKitC-1):

| BME280 | ESP32-S3 |
|---|---|
| VCC | 3V3 |
| GND | GND |
| SDA | GPIO 8 |
| SCL | GPIO 9 |

**Files to add / modify in `main/`:**
- New `bme280.c` / `bme280.h` — thin wrapper around the `bme280` Espressif component (add to `idf_component.yml`). Read T + RH every 2 seconds; store in module-local static atomic values.
- `main.c` — spawn `xTaskCreate(bme280_task, ...)` alongside existing CSI collector task.

## 2. WS2812 zone status LED

**Why:** visible zone status during the pitch (green / amber / red).

**Wiring:** data pin → GPIO 10 (one strip, daisy-chained if multi-zone).

**Files:**
- Reuse ESP-IDF `led_strip` component (already supported; add to `idf_component.yml`).
- `main.c` — subscribe to UDP command socket on port 5006 for color commands from backend (`backend/app/alerts/led_strip.py`, future task). Simple protocol: 3 bytes `R G B`.

## 3. Extended CSI frame (v2)

**Why:** piggy-back BME280 readings on the same UDP stream so the backend has one ingest path.

Upstream frame is version=1 (see RuView ADR-018). VITAL adds version=2 with 8 extra header bytes for temp_x100 (i32 LE) and rh_x100 (u32 LE). Decoder supports both in [`backend/app/ingest/csi_udp.py`](../../backend/app/ingest/csi_udp.py).

**Change in `main/csi_collector.c`:**
- In the UDP send path, bump the version byte to `0x02`.
- Insert 8 bytes after `n_subcarriers` (at offset 10) carrying the latest BME280 reading × 100.
- `n_subcarriers` stays at offset 8 (same as v1). Amplitude+phase arrays shift from offset 10 to offset 18.

## Provisioning

Unchanged — use `provision.py` exactly as upstream:

```bash
python provision.py --port /dev/tty.usbmodem... \
    --ssid "hackupc-2G" --password "..." \
    --target 192.168.1.42 --node-id 1
```

`node_id` = zone index (1-based). Backend maps to `zone-1`, `zone-2`, etc.

## Build

Requires ESP-IDF v5.2+. On mac:

```bash
. $HOME/esp/esp-idf/export.sh
idf.py set-target esp32s3
idf.py build flash monitor
```

## Pre-hackathon acceptance test

1. Flash one ESP32-S3, provision with your phone hotspot.
2. On the laptop: `nc -ul 5005 | xxd | head` — should see frames at ~28 Hz.
3. Start backend (`uvicorn app.main:app`) — `/api/zones` should show the zone with non-zero `bpm` after ~10 s of someone sitting ~1 m from the ESP32.
4. If no breathing signal: check proximity (<2 m), room quiet, and that `esp-csi` Kconfig symbols are enabled in `sdkconfig.defaults`.
