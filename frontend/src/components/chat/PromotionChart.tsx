"use client";
import {
  ComposedChart,
  Bar,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

interface PromotionStat {
  year: number;
  position_from: string;
  position_to: string;
  eligible: number;
  promoted: number;
  rate: number;
  avg_score: number;
  min_score: number;
  my_score?: number | null;
}

interface PromotionChartProps {
  data: PromotionStat[];
}

export default function PromotionChart({ data }: PromotionChartProps) {
  if (!data || data.length === 0) return null;

  const label = `${data[0].position_from} → ${data[0].position_to}`;
  const hasMyScore = data.some((d) => d.my_score != null);

  return (
    <div className="mt-4 pt-3 border-t border-surface-border">
      <p className="text-xs text-gray-400 mb-3 flex items-center gap-1.5">
        <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
        </svg>
        승진 현황 차트 ({label})
      </p>

      {/* Rate + headcount chart */}
      <div className="bg-dark/60 rounded-lg p-3 border border-surface-border/50 mb-3">
        <p className="text-xs text-gray-500 mb-2">승진률 및 인원 추이</p>
        <ResponsiveContainer width="100%" height={200}>
          <ComposedChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#333" />
            <XAxis dataKey="year" tick={{ fill: "#9ca3af", fontSize: 11 }} />
            <YAxis yAxisId="left" tick={{ fill: "#9ca3af", fontSize: 11 }} label={{ value: "명", position: "insideTopLeft", fill: "#9ca3af", fontSize: 10 }} />
            <YAxis yAxisId="right" orientation="right" tick={{ fill: "#9ca3af", fontSize: 11 }} domain={[0, 100]} label={{ value: "%", position: "insideTopRight", fill: "#9ca3af", fontSize: 10 }} />
            <Tooltip
              contentStyle={{ backgroundColor: "#1e1e2e", border: "1px solid #333", borderRadius: 8, fontSize: 12 }}
              labelStyle={{ color: "#e5e7eb" }}
              itemStyle={{ color: "#d1d5db" }}
            />
            <Legend wrapperStyle={{ fontSize: 11, color: "#9ca3af" }} />
            <Bar yAxisId="left" dataKey="eligible" name="대상자" fill="#6366f1" opacity={0.4} radius={[4, 4, 0, 0]} />
            <Bar yAxisId="left" dataKey="promoted" name="승진자" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
            <Line yAxisId="right" type="monotone" dataKey="rate" name="승진률(%)" stroke="#f59e0b" strokeWidth={2} dot={{ r: 4 }} />
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      {/* Score comparison chart */}
      <div className="bg-dark/60 rounded-lg p-3 border border-surface-border/50">
        <p className="text-xs text-gray-500 mb-2">점수 비교 (합격평균 / 합격최저 {hasMyScore ? "/ 내 점수" : ""})</p>
        <ResponsiveContainer width="100%" height={200}>
          <ComposedChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#333" />
            <XAxis dataKey="year" tick={{ fill: "#9ca3af", fontSize: 11 }} />
            <YAxis tick={{ fill: "#9ca3af", fontSize: 11 }} domain={[60, 100]} />
            <Tooltip
              contentStyle={{ backgroundColor: "#1e1e2e", border: "1px solid #333", borderRadius: 8, fontSize: 12 }}
              labelStyle={{ color: "#e5e7eb" }}
              itemStyle={{ color: "#d1d5db" }}
            />
            <Legend wrapperStyle={{ fontSize: 11, color: "#9ca3af" }} />
            <Line type="monotone" dataKey="avg_score" name="합격평균" stroke="#10b981" strokeWidth={2} dot={{ r: 4 }} />
            <Line type="monotone" dataKey="min_score" name="합격최저" stroke="#ef4444" strokeWidth={2} strokeDasharray="5 5" dot={{ r: 4 }} />
            {hasMyScore && (
              <Line type="monotone" dataKey="my_score" name="내 점수" stroke="#f59e0b" strokeWidth={3} dot={{ r: 5, fill: "#f59e0b" }} />
            )}
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
