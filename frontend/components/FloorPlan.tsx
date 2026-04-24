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

export function FloorPlan({ zones }: { zones: Record<string, FusionMessage> }) {
  return (
    <svg viewBox="0 0 620 380" className="w-full h-auto">
      <rect x="0" y="0" width="620" height="380" fill="#0f1620" rx="12" />
      {ZONES.map((z) => {
        const state = zones[z.id];
        const sev = state?.severity ?? "low";
        const fill = severityFill[sev];
        return (
          <g key={z.id}>
            <rect
              x={z.x}
              y={z.y}
              width={z.w}
              height={z.h}
              fill={fill}
              fillOpacity={sev === "low" ? 0.08 : sev === "medium" ? 0.25 : 0.45}
              stroke={fill}
              strokeWidth={sev === "high" ? 3 : 1.5}
              rx="8"
              className={clsx(sev === "high" && "pulse-red")}
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
            {state && state.severity !== "low" && (
              <text
                x={z.x + 12}
                y={z.y + z.h - 14}
                fill={fill}
                fontSize="12"
                fontWeight={700}
              >
                {state.label.toUpperCase()}
              </text>
            )}
          </g>
        );
      })}
    </svg>
  );
}
