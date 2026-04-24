"use client";

import { useEffect, useRef, useState } from "react";
import type { FusionMessage } from "./types";

const DEFAULT_URL =
  process.env.NEXT_PUBLIC_BACKEND_WS ?? "ws://localhost:8000/ws/dashboard";

export function useFusionStream(url: string = DEFAULT_URL) {
  const [zones, setZones] = useState<Record<string, FusionMessage>>({});
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    let closed = false;
    let retry = 0;

    const connect = () => {
      const ws = new WebSocket(url);
      wsRef.current = ws;
      ws.onopen = () => {
        setConnected(true);
        retry = 0;
      };
      ws.onmessage = (e) => {
        try {
          const msg: FusionMessage = JSON.parse(e.data);
          if (msg.type === "fusion") {
            setZones((prev) => ({ ...prev, [msg.zone]: msg }));
          }
        } catch {}
      };
      ws.onclose = () => {
        setConnected(false);
        if (closed) return;
        retry += 1;
        const delay = Math.min(retry * 500, 5000);
        setTimeout(connect, delay);
      };
      ws.onerror = () => ws.close();
    };

    connect();
    return () => {
      closed = true;
      wsRef.current?.close();
    };
  }, [url]);

  return { zones, connected };
}
