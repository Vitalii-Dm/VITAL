"use client";

import clsx from "clsx";
import { motion } from "framer-motion";
import { useEffect, useState } from "react";
import type { FusionMessage } from "@/lib/types";

const severityStyle = {
  low: "border-emerald-600 bg-emerald-950/30",
  medium: "border-amber-500 bg-amber-950/40",
  high: "border-red-500 bg-red-950/50 pulse-red",
};

export function AlertCard({ state }: { state: FusionMessage | undefined }) {
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    if (!state || state.severity === "low") {
      setElapsed(0);
      return;
    }
    const t0 = state.timestamp * 1000;
    const iv = setInterval(() => setElapsed(Date.now() - t0), 100);
    return () => clearInterval(iv);
  }, [state?.zone, state?.severity]);

  if (!state) {
    return (
      <div className="panel p-4 text-gray-500 text-sm">Waiting for sensor data…</div>
    );
  }

  return (
    <motion.div
      layout
      className={clsx(
        "panel p-5 border-2 transition-colors",
        severityStyle[state.severity]
      )}
    >
      <div className="flex items-start justify-between">
        <div>
          <div className="uppercase text-xs tracking-wider text-gray-400">
            {state.zone}
          </div>
          <div className="mt-1 text-xl font-semibold">{state.label}</div>
        </div>
        <span
          className={clsx(
            "text-xs font-bold px-2 py-1 rounded",
            state.severity === "high"
              ? "bg-red-600 text-white"
              : state.severity === "medium"
              ? "bg-amber-500 text-black"
              : "bg-emerald-600 text-white"
          )}
        >
          {state.severity.toUpperCase()}
        </span>
      </div>

      <ul className="mt-3 text-sm text-gray-300 space-y-1">
        {state.reasons.map((r) => (
          <li key={r}>· {r}</li>
        ))}
        {state.reasons.length === 0 && (
          <li className="text-gray-500">All systems normal.</li>
        )}
      </ul>

      <div className="mt-4 flex gap-4 text-xs font-mono text-gray-400">
        <span>Layers: {state.flagged_layers.join(", ") || "—"}</span>
        <span>Confidence: {(state.confidence * 100).toFixed(0)}%</span>
        {state.severity !== "low" && (
          <span className="text-red-400">
            ⏱ {(elapsed / 1000).toFixed(1)}s since event
          </span>
        )}
      </div>
    </motion.div>
  );
}
