"use client";

import dynamic from "next/dynamic";
import type { FlightDailyStatsV1 } from "@/lib/flight-daily-stats";

const Inner = dynamic(() => import("./FlightDailyLineChartInner"), {
  ssr: false,
  loading: () => (
    <div
      className="mt-3 h-[280px] w-full rounded-xl border border-border bg-muted/30 animate-pulse"
      aria-hidden
    />
  ),
});

export interface FlightDailyLineChartProps {
  payload: FlightDailyStatsV1;
}

/**
 * Flight daily row-count line chart (Recharts). Loaded client-only to avoid SSR issues.
 */
export function FlightDailyLineChart({ payload }: FlightDailyLineChartProps) {
  return <Inner payload={payload} />;
}
