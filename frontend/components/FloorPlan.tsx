"use client";

import clsx from "clsx";
import type { FusionMessage } from "@/lib/types";

const ZONES = [
  { id: "zone-1", x: 40, y: 40, w: 180, h: 140, label: "Zone 1 — Aisle A" },
  { id: "zone-2", x: 240, y: 40, w: 180, h: 140, label: "Zone 2 — Aisle B" },
  { id: "zone-3", x: 40, y: 200, w: 180, h: 140, label: "Zone 3 — Packing" },
  { id: "zone-4", x: 240, y: 200, w: 180, h: 140, label: "Zone 4 — Loading" },
  { id: "zone-5", x: 440, y: 40, w: 140, h: 300, label: "Zone 5 — Cold room" },
];

const severityFill: Record<string, string> = {
  low: "#10b981",
  medium: "#f59e0b",
  high: "#ef4444",
};

type DownTier = "none" | "watch" | "warn" | "emergency";

function downTier(max: number | undefined): DownTier {
  if (!max || max < 3) return "none";
  if (max < 10) return "watch";
  if (max < 20) return "warn";
  return "emergency";
}

export function FloorPlan({ zones }: { zones: Record<string, FusionMessage> }) {
  return (
    <svg viewBox="0 0 620 380" className="w-full h-auto">
      <rect x="0" y="0" width="620" height="380" fill="#0f1620" rx="12" />
      {ZONES.map((z) => {
        const state = zones[z.id];
        const sev = state?.severity ?? "low";
        const sevFill = severityFill[sev];
        const tier = downTier(state?.max_down_seconds);
        const stale = state?.pose_stale === true;

        // max_down_seconds >= 20 s overrides severity styling.
        const isEmergencyOverride = tier === "emergency";
        const strokeColor = isEmergencyOverride
          ? severityFill.high
          : tier === "warn"
          ? severityFill.medium
          : tier === "watch"
          ? "#eab308"
          : sevFill;

        const strokeWidth =
          isEmergencyOverride || sev === "high" ? 3 : tier === "warn" ? 2.5 : 1.5;

        const showAmberGlow = tier === "warn" && !isEmergencyOverride;

        return (
          <g key={z.id}>
            <rect
              x={z.x}
              y={z.y}
              width={z.w}
              height={z.h}
              fill={sevFill}
              fillOpacity={sev === "low" ? 0.08 : sev === "medium" ? 0.25 : 0.45}
              stroke={strokeColor}
              strokeWidth={strokeWidth}
              rx="8"
              className={clsx(
                isEmergencyOverride && "zone-down-flash",
                !isEmergencyOverride && sev === "high" && "pulse-red",
                showAmberGlow && "animate-pulse"
              )}
              strokeDasharray={tier === "watch" && !isEmergencyOverride ? "6 4" : undefined}
            />
            <text
              x={z.x + 12}
              y={z.y + 24}
              fill="#e5e7eb"
              fontSize="13"
              fontWeight={600}
            >
              {z.label}
            </text>
            {state && (
              <text
                x={z.x + 12}
                y={z.y + 44}
                fill="#9ca3af"
                fontSize="11"
                fontFamily="ui-monospace"
              >
                {state.bpm > 0 ? `${state.bpm.toFixed(0)} bpm · ` : ""}
                {state.temp_c.toFixed(0)}°C · WBT {state.wetbulb_c.toFixed(0)}°
              </text>
            )}
            {state && (
              <text
                x={z.x + 12}
                y={z.y + 60}
                fill="#6b7280"
                fontSize="10"
                fontFamily="ui-monospace"
              >
                Standing: {state.standing_count ?? 0} · Floor:{" "}
                {(state.persons ?? []).filter(
                  (p) => (p.down_seconds ?? 0) >= 3
                ).length}
              </text>
            )}
            {state && state.severity !== "low" && (
              <text
                x={z.x + 12}
                y={z.y + z.h - 14}
                fill={sevFill}
                fontSize="12"
                fontWeight={700}
              >
                {state.label.toUpperCase()}
              </text>
            )}
            {tier !== "none" && (
              <g>
                <rect
                  x={z.x + z.w - 104}
                  y={z.y + 8}
                  width={96}
                  height={20}
                  rx={4}
                  fill={
                    isEmergencyOverride
                      ? "#ef4444"
                      : tier === "warn"
                      ? "#f59e0b"
                      : "#eab308"
                  }
                  fillOpacity={0.9}
                />
                <text
                  x={z.x + z.w - 56}
                  y={z.y + 22}
                  fill={isEmergencyOverride ? "#fff" : "#111"}
                  fontSize="10"
                  fontWeight={700}
                  textAnchor="middle"
                  fontFamily="ui-monospace"
                >
                  {isEmergencyOverride
                    ? `EMERGENCY ${Math.round(state?.max_down_seconds ?? 0)}s`
                    : `DOWN ${Math.round(state?.max_down_seconds ?? 0)}s`}
                </text>
              </g>
            )}
            {stale && (
              <g>
                <rect
                  x={z.x + 12}
                  y={z.y + z.h - 34}
                  width={112}
                  height={18}
                  rx={4}
                  fill="#374151"
                  stroke="#4b5563"
                  strokeWidth={1}
                />
                <text
                  x={z.x + 68}
                  y={z.y + z.h - 21}
                  fill="#d1d5db"
                  fontSize="10"
                  fontWeight={600}
                  textAnchor="middle"
                  fontFamily="ui-monospace"
                >
                  CAMERA OFFLINE
                </text>
              </g>
            )}
          </g>
        );
      })}
    </svg>
  );
}
