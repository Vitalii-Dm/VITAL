export type Severity = "low" | "medium" | "high";

export type EventType =
  | "normal"
  | "fall"
  | "heat_exhaustion"
  | "cardiac"
  | "loss_of_consciousness"
  | "unknown_medical";

export type Keypoint = [number, number, number];

export type Posture = "standing" | "on_floor" | "unknown";

export interface Person {
  track_id: number;
  horizontal: boolean;
  down_seconds: number;
  // Optional for backwards compat with pre-standing emitters — treat
  // absence as "unknown" / false.
  posture?: Posture;
  standing?: boolean;
  keypoints: Keypoint[];
}

export interface FusionMessage {
  type: "fusion";
  zone: string;
  severity: Severity;
  event: EventType;
  label: string;
  confidence: number;
  flagged_layers: string[];
  reasons: string[];
  timestamp: number;
  bpm: number;
  temp_c: number;
  rh_pct: number;
  wetbulb_c: number;
  waveform: number[];
  persons?: Person[];
  max_down_seconds?: number;
  standing_count?: number;
  pose_stale?: boolean;
}
