export type Severity = "low" | "medium" | "high";

export type EventType =
  | "normal"
  | "fall"
  | "heat_exhaustion"
  | "cardiac"
  | "loss_of_consciousness"
  | "unknown_medical";

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
}
