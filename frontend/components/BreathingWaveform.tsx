"use client";

import { LineChart, Line, ResponsiveContainer, YAxis } from "recharts";

export function BreathingWaveform({ data }: { data: number[] }) {
  const chartData = data.map((y, i) => ({ i, y }));
  return (
    <div className="h-32">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={chartData}>
          <YAxis hide domain={["dataMin", "dataMax"]} />
          <Line
            type="monotone"
            dataKey="y"
            stroke="#60a5fa"
            strokeWidth={2}
            dot={false}
            isAnimationActive={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
