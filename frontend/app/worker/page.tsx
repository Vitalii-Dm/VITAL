"use client";

import { useFusionStream } from "@/lib/useFusionStream";

function heatAdvice(wbt: number): { level: string; color: string; msg: string } {
  if (wbt < 25) return { level: "Safe", color: "text-emerald-400", msg: "Conditions are fine. Keep hydrating." };
  if (wbt < 28) return { level: "Elevated", color: "text-amber-400", msg: "It's warm. Take a 5-minute break every hour." };
  if (wbt < 32) return { level: "High", color: "text-orange-400", msg: "Heat stress rising — take a 10-minute break now and hydrate." };
  return { level: "Extreme", color: "text-red-400", msg: "Stop work. Move to a cooler area immediately." };
}

export default function Worker() {
  const { zones } = useFusionStream();
  const zone = Object.values(zones)[0];
  const advice = zone ? heatAdvice(zone.wetbulb_c) : null;

  return (
    <main className="min-h-screen p-6 max-w-md mx-auto">
      <h1 className="text-2xl font-bold">VITAL · worker</h1>
      <p className="text-gray-400 text-sm">
        Personal heat-stress monitor. Your privacy is respected — this app shows only
        your zone&apos;s conditions.
      </p>

      <section className="panel p-5 mt-6">
        <div className="text-xs uppercase tracking-wider text-gray-400">
          Current zone
        </div>
        <div className="text-2xl font-semibold">{zone?.zone ?? "—"}</div>

        <div className="mt-4 grid grid-cols-3 gap-3 text-center">
          <div>
            <div className="text-xs text-gray-500">Temp</div>
            <div className="text-xl font-mono">
              {zone ? `${zone.temp_c.toFixed(0)}°` : "—"}
            </div>
          </div>
          <div>
            <div className="text-xs text-gray-500">Humidity</div>
            <div className="text-xl font-mono">
              {zone ? `${zone.rh_pct.toFixed(0)}%` : "—"}
            </div>
          </div>
          <div>
            <div className="text-xs text-gray-500">Wet-bulb</div>
            <div className="text-xl font-mono">
              {zone ? `${zone.wetbulb_c.toFixed(0)}°` : "—"}
            </div>
          </div>
        </div>
      </section>

      {advice && (
        <section className="panel p-5 mt-4">
          <div className={`text-xs uppercase tracking-wider ${advice.color}`}>
            Heat stress · {advice.level}
          </div>
          <p className="mt-2 text-gray-200">{advice.msg}</p>
        </section>
      )}
    </main>
  );
}
