"use client";

import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import type { FlightDailyStatsV1 } from "@/lib/flight-daily-stats";

export interface FlightDailyLineChartInnerProps {
  payload: FlightDailyStatsV1;
}

export default function FlightDailyLineChartInner({
  payload,
}: FlightDailyLineChartInnerProps) {
  const data = payload.series.map((p) => ({
    date: p.date,
    count: p.count,
  }));

  const rangeLabel =
    payload.range != null
      ? `${payload.range.start} — ${payload.range.end}`
      : "";

  return (
    <Card className="mt-3 border bg-card/80 shadow-sm">
      <CardHeader className="pb-2">
        <CardTitle className="text-base font-semibold">
          飞行动态 · 每日数据条数
        </CardTitle>
        {rangeLabel ? (
          <CardDescription className="text-xs text-muted-foreground">
            统计区间（UTC 日期）: {rangeLabel}
          </CardDescription>
        ) : null}
      </CardHeader>
      <CardContent className="pt-0">
        {data.length === 0 ? (
          <p className="text-sm text-muted-foreground py-8 text-center">
            该时间范围内暂无按日汇总数据
          </p>
        ) : (
          <div className="h-[280px] w-full min-w-0">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart
                data={data}
                margin={{ top: 8, right: 12, left: 0, bottom: 8 }}
              >
                <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
                <XAxis
                  dataKey="date"
                  tick={{ fontSize: 11 }}
                  className="text-muted-foreground"
                  interval="preserveStartEnd"
                />
                <YAxis
                  tick={{ fontSize: 11 }}
                  className="text-muted-foreground"
                  allowDecimals={false}
                />
                <Tooltip
                  contentStyle={{
                    borderRadius: "8px",
                    border: "1px solid hsl(var(--border))",
                    background: "hsl(var(--card))",
                  }}
                  labelFormatter={(label) => `日期: ${label}`}
                  formatter={(value: number) => [`${value}`, "条数"]}
                />
                <Line
                  type="monotone"
                  dataKey="count"
                  stroke="hsl(var(--primary))"
                  strokeWidth={2}
                  dot={{ r: 3 }}
                  activeDot={{ r: 5 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
