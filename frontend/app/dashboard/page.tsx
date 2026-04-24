"use client";

import { AlertCard } from "@/components/AlertCard";
import { BreathingWaveform } from "@/components/BreathingWaveform";
import { FloorPlan } from "@/components/FloorPlan";
import { useFusionStream } from "@/lib/useFusionStream";

export default function Dashboard() {
  const { zones, connected } = useFusionStream();
  const primary = Object.values(zones)[0];

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
            </div>
          ))}
          {Object.keys(zones).length === 0 && (
            <div className="col-span-full text-gray-500 text-sm">
              No zones reporting yet.
            </div>
          )}
        </div>
      </section>
    </main>
  );
}
