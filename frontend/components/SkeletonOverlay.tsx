"use client";

import clsx from "clsx";
import type { Person } from "@/lib/types";

// COCO-17 keypoint indices
// 0 nose, 1 left_eye, 2 right_eye, 3 left_ear, 4 right_ear,
// 5 left_shoulder, 6 right_shoulder, 7 left_elbow, 8 right_elbow,
// 9 left_wrist, 10 right_wrist, 11 left_hip, 12 right_hip,
// 13 left_knee, 14 right_knee, 15 left_ankle, 16 right_ankle
const COCO_EDGES: Array<[number, number]> = [
  // face
  [0, 1], [0, 2], [1, 3], [2, 4],
  // torso
  [5, 6], [5, 11], [6, 12], [11, 12],
  // left arm
  [5, 7], [7, 9],
  // right arm
  [6, 8], [8, 10],
  // left leg
  [11, 13], [13, 15],
  // right leg
  [12, 14], [14, 16],
];

const KP_CONF_THRESHOLD = 0.3;

type BadgeTier = "none" | "yellow" | "amber" | "red";

function badgeTier(downSeconds: number): BadgeTier {
  if (downSeconds < 3) return "none";
  if (downSeconds < 10) return "yellow";
  if (downSeconds < 20) return "amber";
  return "red";
}

function headAnchor(keypoints: Person["keypoints"]): { x: number; y: number } | null {
  if (!keypoints || keypoints.length < 17) return null;
  const nose = keypoints[0];
  if (nose && nose[2] >= KP_CONF_THRESHOLD) {
    return { x: nose[0], y: nose[1] };
  }
  const ls = keypoints[5];
  const rs = keypoints[6];
  if (ls && rs && ls[2] >= KP_CONF_THRESHOLD && rs[2] >= KP_CONF_THRESHOLD) {
    return { x: (ls[0] + rs[0]) / 2, y: (ls[1] + rs[1]) / 2 - 30 };
  }
  return null;
}

function PersonSkeleton({ person }: { person: Person }) {
  const { keypoints } = person;
  const tier = badgeTier(person.down_seconds);
  // Down-tier stroke wins — those are the risk states the dashboard
  // already colours. Otherwise the stroke reflects posture: green for
  // standing, slate for unknown (so operators can tell the CV layer is
  // uncertain from a glance), blue as the legacy default.
  const downStroke =
    tier === "red"
      ? { color: "#ef4444", opacity: 0.9 }
      : tier === "amber"
      ? { color: "#f59e0b", opacity: 0.9 }
      : tier === "yellow"
      ? { color: "#eab308", opacity: 0.9 }
      : null;
  const postureStroke =
    person.posture === "standing" || person.standing === true
      ? { color: "#34d399", opacity: 0.7 } // emerald-400
      : person.posture === "unknown"
      ? { color: "#94a3b8", opacity: 0.8 } // slate-400
      : { color: "#60a5fa", opacity: 0.9 }; // default blue

  const { color: stroke, opacity: strokeOpacity } =
    downStroke ?? postureStroke;

  return (
    <g>
      {COCO_EDGES.map(([a, b], i) => {
        const ka = keypoints[a];
        const kb = keypoints[b];
        if (!ka || !kb) return null;
        if (ka[2] < KP_CONF_THRESHOLD || kb[2] < KP_CONF_THRESHOLD) return null;
        return (
          <line
            key={i}
            x1={ka[0]}
            y1={ka[1]}
            x2={kb[0]}
            y2={kb[1]}
            stroke={stroke}
            strokeWidth={3}
            strokeLinecap="round"
            opacity={strokeOpacity}
          />
        );
      })}
      {keypoints.map((kp, i) => {
        if (!kp || kp[2] < KP_CONF_THRESHOLD) return null;
        return (
          <circle
            key={i}
            cx={kp[0]}
            cy={kp[1]}
            r={4}
            fill={stroke}
            stroke="#0b0f14"
            strokeWidth={1}
          />
        );
      })}
    </g>
  );
}

function PersonBadge({ person }: { person: Person }) {
  const tier = badgeTier(person.down_seconds);
  if (tier === "none") return null;
  const anchor = headAnchor(person.keypoints);
  if (!anchor) return null;

  const seconds = Math.round(person.down_seconds);
  const text = tier === "red" ? `EMERGENCY · ${seconds}s` : `DOWN · ${seconds}s`;

  const color =
    tier === "red"
      ? "bg-red-600 text-white"
      : tier === "amber"
      ? "bg-amber-500 text-black"
      : "bg-yellow-400 text-black";

  const pulse =
    tier === "red"
      ? "skeleton-pulse-fast"
      : tier === "amber"
      ? "animate-pulse"
      : "";

  const sizing =
    tier === "red"
      ? "text-[13px] px-2.5 py-1 font-bold"
      : "text-[11px] px-2 py-0.5 font-semibold";

  // SVG <foreignObject> lets us reuse Tailwind for badge styling.
  const bw = tier === "red" ? 150 : 110;
  const bh = tier === "red" ? 28 : 22;
  const x = anchor.x - bw / 2;
  const y = anchor.y - bh - 14;

  return (
    <foreignObject x={x} y={y} width={bw} height={bh} style={{ overflow: "visible" }}>
      <div
        className={clsx(
          "rounded-md shadow-lg tracking-wide whitespace-nowrap inline-block",
          color,
          pulse,
          sizing
        )}
      >
        {text}
      </div>
    </foreignObject>
  );
}

export interface SkeletonOverlayProps {
  persons: Person[];
  width?: number;
  height?: number;
  className?: string;
}

export function SkeletonOverlay({
  persons,
  width = 640,
  height = 480,
  className,
}: SkeletonOverlayProps) {
  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      preserveAspectRatio="xMidYMid meet"
      className={clsx("w-full h-auto", className)}
    >
      <rect
        x={0}
        y={0}
        width={width}
        height={height}
        fill="#0b0f14"
        stroke="#1f2a37"
        strokeWidth={1}
        rx={10}
      />
      {persons.map((p) => (
        <PersonSkeleton key={p.track_id} person={p} />
      ))}
      {persons.map((p) => (
        <PersonBadge key={`b-${p.track_id}`} person={p} />
      ))}
      {persons.length === 0 && (
        <text
          x={width / 2}
          y={height / 2}
          fill="#4b5563"
          fontSize={14}
          textAnchor="middle"
          fontFamily="ui-monospace"
        >
          no persons detected
        </text>
      )}
    </svg>
  );
}
