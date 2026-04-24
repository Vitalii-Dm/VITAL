"use client";

import { AlertCard } from "@/components/AlertCard";
import { BreathingWaveform } from "@/components/BreathingWaveform";
import { FloorPlan } from "@/components/FloorPlan";
import { SkeletonOverlay } from "@/components/SkeletonOverlay";
import { useFusionStream } from "@/lib/useFusionStream";
import type { FusionMessage } from "@/lib/types";

function pickFocus(zones: Record<string, FusionMessage>): FusionMessage | undefined {
  const values = Object.values(zones);
  if (values.length === 0) return undefined;
  // Prefer zones where someone is down the longest; fall back to first.
  const sorted = [...values].sort(
    (a, b) => (b.max_down_seconds ?? 0) - (a.max_down_seconds ?? 0)
  );
  return sorted[0];
}

export default function Dashboard() {
  const { zones, connected } = useFusionStream();
  const primary = pickFocus(zones);
  const zonesWithPeople = Object.values(zones).filter(
    (z) => !z.pose_stale && (z.persons?.length ?? 0) > 0
  );

  return (
    <main className="min-h-screen p-8 grid grid-cols-12 gap-6">
      <header className="col-span-12 flex items-baseline justify-between">
        <div>
          <h1 className="text-3xl font-bold">VITAL · supervisor</h1>
          <p className="text-gray-400 text-sm">
            Warehouse floor — real-time worker safety monitoring
          </p>
        </div>
        <div className="text-xs font-mono">
          <span
            className={
              connected ? "text-emerald-400" : "text-red-400"
            }
          >
            ● {connected ? "LIVE" : "DISCONNECTED"}
          </span>
        </div>
      </header>

      <section className="col-span-12 lg:col-span-8 panel p-4">
        <h2 className="text-sm uppercase tracking-wider text-gray-400 mb-2">
          Floor plan
        </h2>
        <FloorPlan zones={zones} />
      </section>

      <aside className="col-span-12 lg:col-span-4 flex flex-col gap-4">
        <AlertCard state={primary} />
        <div className="panel p-4">
          <h3 className="text-xs uppercase tracking-wider text-gray-400">
            Breathing waveform (WiFi CSI)
          </h3>
          <BreathingWaveform data={primary?.waveform ?? []} />
          <div className="text-xs font-mono text-gray-400 mt-2">
            {primary?.bpm ? `${primary.bpm.toFixed(1)} BPM` : "— bpm"} ·{" "}
            {primary ? `${primary.temp_c.toFixed(1)}°C / ${primary.rh_pct.toFixed(0)}% RH` : ""}
          </div>
        </div>
        <div className="panel p-4">
          <div className="flex items-baseline justify-between mb-2">
            <h3 className="text-xs uppercase tracking-wider text-gray-400">
              Pose · {primary?.zone ?? "—"}
            </h3>
            {primary?.pose_stale && (
              <span className="text-[10px] font-mono text-gray-400 bg-gray-700/60 px-2 py-0.5 rounded">
                CAMERA OFFLINE
              </span>
            )}
          </div>
          {primary && !primary.pose_stale ? (
            <SkeletonOverlay persons={primary.persons ?? []} />
          ) : (
            <div className="aspect-[4/3] flex items-center justify-center text-gray-500 text-sm border border-gray-800 rounded-lg">
              {primary?.pose_stale ? "Camera offline" : "Waiting for pose stream…"}
            </div>
          )}
          {primary && !primary.pose_stale && (
            <div className="text-xs font-mono text-gray-400 mt-2">
              {(primary.persons?.length ?? 0)} person
              {(primary.persons?.length ?? 0) === 1 ? "" : "s"}
              {typeof primary.max_down_seconds === "number" && primary.max_down_seconds >= 1
                ? ` · max down ${primary.max_down_seconds.toFixed(1)}s`
                : ""}
            </div>
          )}
        </div>
      </aside>

      <section className="col-span-12 panel p-4">
        <h3 className="text-sm uppercase tracking-wider text-gray-400 mb-3">
          All zones
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
          {Object.values(zones).map((z) => (
            <div key={z.zone} className="rounded-lg border border-gray-800 p-3">
              <div className="text-xs text-gray-400">{z.zone}</div>
              <div className="text-lg font-semibold">{z.label}</div>
              <div className="text-xs font-mono text-gray-400 mt-1">
                {z.bpm > 0 ? `${z.bpm.toFixed(0)} bpm` : "—"} · WBT {z.wetbulb_c.toFixed(0)}°
              </div>
              {typeof z.max_down_seconds === "number" && z.max_down_seconds >= 3 && (
                <div
                  className={
                    "text-[10px] font-mono mt-1 " +
                    (z.max_down_seconds >= 20
                      ? "text-red-400"
                      : z.max_down_seconds >= 10
                      ? "text-amber-400"
                      : "text-yellow-300")
                  }
                >
                  down {z.max_down_seconds.toFixed(0)}s
                </div>
              )}
              {z.pose_stale && (
                <div className="text-[10px] font-mono text-gray-500 mt-1">camera offline</div>
              )}
            </div>
          ))}
          {Object.keys(zones).length === 0 && (
            <div className="col-span-full text-gray-500 text-sm">
              No zones reporting yet.
            </div>
          )}
        </div>

        {zonesWithPeople.length > 1 && (
          <div className="mt-6">
            <h4 className="text-xs uppercase tracking-wider text-gray-400 mb-3">
              Live skeletons
            </h4>
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
              {zonesWithPeople.map((z) => (
                <div key={`sk-${z.zone}`} className="rounded-lg border border-gray-800 p-2">
                  <div className="text-xs text-gray-400 mb-1">{z.zone}</div>
                  <SkeletonOverlay persons={z.persons ?? []} />
                </div>
              ))}
            </div>
          </div>
        )}
      </section>
    </main>
  );
}
