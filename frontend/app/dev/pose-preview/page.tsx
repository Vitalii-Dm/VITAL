"use client";

// Dev-only harness. Renders the dashboard visuals from canned fixtures so
// we can eyeball SkeletonOverlay + FloorPlan states without a live backend.
// Not linked from production navigation.

import { AlertCard } from "@/components/AlertCard";
import { FloorPlan } from "@/components/FloorPlan";
import { SkeletonOverlay } from "@/components/SkeletonOverlay";
import { fusionFixtures } from "@/lib/__fixtures__/fusion";

export default function PosePreview() {
  const zones = fusionFixtures;
  const entries = Object.values(zones);

  return (
    <main className="min-h-screen p-8 flex flex-col gap-6">
      <header>
        <h1 className="text-2xl font-bold">VITAL · pose preview (dev)</h1>
        <p className="text-gray-400 text-sm">
          Static fixture render — no WS. Covers all four down-tiers + stale camera.
        </p>
      </header>

      <section className="panel p-4">
        <h2 className="text-sm uppercase tracking-wider text-gray-400 mb-2">
          Floor plan
        </h2>
        <FloorPlan zones={zones} />
      </section>

      <section className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {entries.map((z) => (
          <div key={z.zone} className="flex flex-col gap-3">
            <AlertCard state={z} />
            <div className="panel p-3">
              <div className="text-xs text-gray-400 mb-1">
                {z.zone}
                {z.pose_stale ? " · camera offline" : ""}
              </div>
              {z.pose_stale ? (
                <div className="aspect-[4/3] flex items-center justify-center text-gray-500 text-sm border border-gray-800 rounded-lg">
                  Camera offline
                </div>
              ) : (
                <SkeletonOverlay persons={z.persons ?? []} />
              )}
              <div className="text-xs font-mono text-gray-400 mt-1">
                max_down_seconds = {(z.max_down_seconds ?? 0).toFixed(1)}s
              </div>
            </div>
          </div>
        ))}
      </section>
    </main>
  );
}
