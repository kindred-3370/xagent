/**
 * Extract flight daily stats payload from chat trace events (tool_execution_end).
 * Only matches get_flight_dynamic_daily_stats + schema_version flight_daily_stats_v1.
 */

export const FLIGHT_DAILY_STATS_SCHEMA_V1 = "flight_daily_stats_v1" as const;
export const FLIGHT_DYNAMIC_STATS_TOOL_NAME = "get_flight_dynamic_daily_stats" as const;

export interface FlightDailyStatsRange {
  start: string;
  end: string;
}

export interface FlightDailyStatsPoint {
  date: string;
  count: number;
}

export interface FlightDailyStatsV1 {
  schema_version: typeof FLIGHT_DAILY_STATS_SCHEMA_V1;
  success: boolean;
  range: FlightDailyStatsRange | null;
  series: FlightDailyStatsPoint[];
  message?: string;
  error?: string | null;
  row_count?: number;
}

interface TraceEventLike {
  event_type?: string;
  data?: {
    tool_name?: string;
    result?: unknown;
    success?: boolean;
    [key: string]: unknown;
  };
}

function normalizeToolResult(raw: unknown): Record<string, unknown> | null {
  if (raw == null) return null;
  if (typeof raw === "string") {
    try {
      return JSON.parse(raw) as Record<string, unknown>;
    } catch {
      return null;
    }
  }
  if (typeof raw === "object" && !Array.isArray(raw)) {
    return raw as Record<string, unknown>;
  }
  return null;
}

/** Pydantic RootModel[dict] often serializes as { root: { ... } }. */
function unwrapPydanticRoot(obj: Record<string, unknown>): Record<string, unknown> {
  const inner = obj.root;
  if (
    inner != null &&
    typeof inner === "object" &&
    !Array.isArray(inner)
  ) {
    return inner as Record<string, unknown>;
  }
  return obj;
}

function isValidSeries(
  series: unknown
): series is FlightDailyStatsPoint[] {
  if (!Array.isArray(series)) return false;
  for (const item of series) {
    if (item == null || typeof item !== "object") return false;
    const o = item as Record<string, unknown>;
    if (typeof o.date !== "string" || o.date.length < 8) return false;
    if (typeof o.count !== "number" || Number.isNaN(o.count)) return false;
  }
  return true;
}

function coercePayload(obj: Record<string, unknown>): FlightDailyStatsV1 | null {
  if (obj.schema_version !== FLIGHT_DAILY_STATS_SCHEMA_V1) return null;
  if (obj.success !== true) return null;
  if (!isValidSeries(obj.series)) return null;
  const rangeRaw = obj.range;
  let range: FlightDailyStatsRange | null = null;
  if (
    rangeRaw != null &&
    typeof rangeRaw === "object" &&
    typeof (rangeRaw as FlightDailyStatsRange).start === "string" &&
    typeof (rangeRaw as FlightDailyStatsRange).end === "string"
  ) {
    range = {
      start: (rangeRaw as FlightDailyStatsRange).start,
      end: (rangeRaw as FlightDailyStatsRange).end,
    };
  }
  return {
    schema_version: FLIGHT_DAILY_STATS_SCHEMA_V1,
    success: true,
    range,
    series: obj.series as FlightDailyStatsPoint[],
    message: typeof obj.message === "string" ? obj.message : undefined,
    error: obj.error === null || typeof obj.error === "string" ? (obj.error as string | null) : null,
    row_count: typeof obj.row_count === "number" ? obj.row_count : obj.series.length,
  };
}

/**
 * Returns the last successful flight daily stats payload from trace events, if any.
 */
export function extractFlightDailyStatsFromTraceEvents(
  events: TraceEventLike[] | undefined | null
): FlightDailyStatsV1 | null {
  if (!events || !Array.isArray(events)) return null;
  let last: FlightDailyStatsV1 | null = null;
  for (const ev of events) {
    if (ev?.event_type !== "tool_execution_end") continue;
    const toolName = ev.data?.tool_name;
    if (toolName !== FLIGHT_DYNAMIC_STATS_TOOL_NAME) continue;
    const raw = normalizeToolResult(ev.data?.result);
    if (!raw) continue;
    const payload = coercePayload(unwrapPydanticRoot(raw));
    if (payload) last = payload;
  }
  return last;
}
