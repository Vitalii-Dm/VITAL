// Dev/test-only fixtures. Do not import from production code paths.
// Used by dev harnesses to eyeball SkeletonOverlay + floor-plan states
// without a live backend. Matches shared/schema.md + Person type.

import type { FusionMessage, Person } from "../types";

function standingPose(cx: number, cy: number): Person["keypoints"] {
  // COCO-17 upright. cy = approx head-top.
  return [
    [cx,       cy,        0.95], // 0  nose
    [cx - 8,   cy - 4,    0.90], // 1  left_eye
    [cx + 8,   cy - 4,    0.90], // 2  right_eye
    [cx - 14,  cy + 2,    0.80], // 3  left_ear
    [cx + 14,  cy + 2,    0.80], // 4  right_ear
    [cx - 30,  cy + 50,   0.92], // 5  left_shoulder
    [cx + 30,  cy + 50,   0.92], // 6  right_shoulder
    [cx - 45,  cy + 110,  0.88], // 7  left_elbow
    [cx + 45,  cy + 110,  0.88], // 8  right_elbow
    [cx - 55,  cy + 170,  0.82], // 9  left_wrist
    [cx + 55,  cy + 170,  0.82], // 10 right_wrist
    [cx - 22,  cy + 180,  0.90], // 11 left_hip
    [cx + 22,  cy + 180,  0.90], // 12 right_hip
    [cx - 26,  cy + 260,  0.86], // 13 left_knee
    [cx + 26,  cy + 260,  0.86], // 14 right_knee
    [cx - 30,  cy + 340,  0.80], // 15 left_ankle
    [cx + 30,  cy + 340,  0.80], // 16 right_ankle
  ];
}

function horizontalPose(cx: number, cy: number): Person["keypoints"] {
  // Rotated 90°: head to the right, feet to the left, person lying on floor.
  return [
    [cx + 180, cy,        0.92], // 0  nose
    [cx + 184, cy - 8,    0.85], // 1  left_eye
    [cx + 184, cy + 8,    0.85], // 2  right_eye
    [cx + 170, cy - 14,   0.75], // 3  left_ear
    [cx + 170, cy + 14,   0.75], // 4  right_ear
    [cx + 130, cy - 30,   0.90], // 5  left_shoulder
    [cx + 130, cy + 30,   0.90], // 6  right_shoulder
    [cx + 70,  cy - 45,   0.85], // 7  left_elbow
    [cx + 70,  cy + 45,   0.85], // 8  right_elbow
    [cx + 10,  cy - 55,   0.78], // 9  left_wrist
    [cx + 10,  cy + 55,   0.78], // 10 right_wrist
    [cx,       cy - 22,   0.88], // 11 left_hip
    [cx,       cy + 22,   0.88], // 12 right_hip
    [cx - 80,  cy - 26,   0.84], // 13 left_knee
    [cx - 80,  cy + 26,   0.84], // 14 right_knee
    [cx - 160, cy - 30,   0.76], // 15 left_ankle
    [cx - 160, cy + 30,   0.76], // 16 right_ankle
  ];
}

export const standingPerson: Person = {
  track_id: 1,
  horizontal: false,
  down_seconds: 0,
  posture: "standing",
  standing: true,
  keypoints: standingPose(320, 60),
};

export const secondStandingPerson: Person = {
  track_id: 5,
  horizontal: false,
  down_seconds: 0,
  posture: "standing",
  standing: true,
  keypoints: standingPose(140, 60),
};

export const downWatchPerson: Person = {
  track_id: 2,
  horizontal: true,
  down_seconds: 6.1,
  posture: "on_floor",
  standing: false,
  keypoints: horizontalPose(260, 260),
};

export const downWarnPerson: Person = {
  track_id: 3,
  horizontal: true,
  down_seconds: 14.7,
  posture: "on_floor",
  standing: false,
  keypoints: horizontalPose(260, 260),
};

export const emergencyPerson: Person = {
  track_id: 4,
  horizontal: true,
  down_seconds: 27.3,
  posture: "on_floor",
  standing: false,
  keypoints: horizontalPose(260, 260),
};

function baseFusion(zone: string): FusionMessage {
  return {
    type: "fusion",
    zone,
    severity: "low",
    event: "normal",
    label: "All clear",
    confidence: 0.1,
    flagged_layers: [],
    reasons: [],
    timestamp: Date.now() / 1000,
    bpm: 16,
    temp_c: 24,
    rh_pct: 50,
    wetbulb_c: 18,
    waveform: Array.from({ length: 120 }, (_, i) => Math.sin(i / 6) * 0.5),
    persons: [],
    max_down_seconds: 0,
    standing_count: 0,
    pose_stale: false,
  };
}

export const fusionFixtures: Record<string, FusionMessage> = {
  "zone-1": {
    ...baseFusion("zone-1"),
    label: "Two workers upright",
    persons: [standingPerson, secondStandingPerson],
    max_down_seconds: 0,
    standing_count: 2,
  },
  "zone-2": {
    ...baseFusion("zone-2"),
    severity: "medium",
    event: "unknown_medical",
    label: "Worker down (watch)",
    reasons: ["person horizontal (6s)"],
    confidence: 0.6,
    persons: [downWatchPerson, secondStandingPerson],
    max_down_seconds: 6.1,
    standing_count: 1,
  },
  "zone-3": {
    ...baseFusion("zone-3"),
    severity: "medium",
    event: "fall",
    label: "Worker down (warn)",
    reasons: ["person horizontal (15s)", "no breathing signal"],
    confidence: 0.78,
    bpm: 0,
    persons: [downWarnPerson],
    max_down_seconds: 14.7,
    standing_count: 0,
  },
  "zone-4": {
    ...baseFusion("zone-4"),
    severity: "high",
    event: "loss_of_consciousness",
    label: "Possible LOC",
    reasons: ["person horizontal (27s)", "breathing absent", "no recovery"],
    confidence: 0.92,
    bpm: 0,
    persons: [emergencyPerson],
    max_down_seconds: 27.3,
    standing_count: 0,
  },
  "zone-5": {
    ...baseFusion("zone-5"),
    label: "Camera offline",
    persons: [],
    max_down_seconds: 0,
    standing_count: 0,
    pose_stale: true,
  },
};
