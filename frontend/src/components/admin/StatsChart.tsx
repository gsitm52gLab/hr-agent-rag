"use client";
import { useEffect, useState } from "react";
import { getStats } from "@/lib/api";
import type { SearchStats } from "@/lib/types";

export default function StatsChart() {
  const [stats, setStats] = useState<SearchStats | null>(null);

  useEffect(() => {
    getStats().then(setStats).catch(() => {});
  }, []);

  if (!stats) {
    return <div className="text-gray-500 text-center py-8">통계 로딩 중...</div>;
  }

  const maxDaily = Math.max(...stats.daily_stats.map((d) => d.count), 1);

  return (
    <div className="space-y-6">
      {/* Summary cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-surface border border-surface-border rounded-xl p-5">
          <p className="text-gray-400 text-sm">총 검색 횟수</p>
          <p className="text-3xl font-bold text-white mt-1">{stats.total_queries}</p>
        </div>
        <div className="bg-surface border border-surface-border rounded-xl p-5">
          <p className="text-gray-400 text-sm">평균 응답 시간</p>
          <p className="text-3xl font-bold text-white mt-1">{stats.avg_response_time_ms}ms</p>
        </div>
        <div className="bg-surface border border-surface-border rounded-xl p-5">
          <p className="text-gray-400 text-sm">인기 검색어 수</p>
          <p className="text-3xl font-bold text-white mt-1">{stats.top_queries.length}</p>
        </div>
      </div>

      {/* Daily chart (simple bar chart) */}
      {stats.daily_stats.length > 0 && (
        <div className="bg-surface border border-surface-border rounded-xl p-5">
          <h3 className="text-white font-medium mb-4">일별 검색 추이</h3>
          <div className="flex items-end gap-1 h-40">
            {stats.daily_stats.slice(-14).reverse().map((d, i) => (
              <div key={i} className="flex-1 flex flex-col items-center gap-1">
                <div
                  className="w-full bg-gradient-to-t from-purple-600 to-blue-600 rounded-t-sm min-h-[2px]"
                  style={{ height: `${(d.count / maxDaily) * 100}%` }}
                />
                <span className="text-[10px] text-gray-500 rotate-[-45deg] origin-top-left whitespace-nowrap">
                  {d.date.slice(5)}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Top queries */}
      {stats.top_queries.length > 0 && (
        <div className="bg-surface border border-surface-border rounded-xl p-5">
          <h3 className="text-white font-medium mb-4">인기 검색어</h3>
          <div className="space-y-2">
            {stats.top_queries.map((q, i) => (
              <div key={i} className="flex items-center gap-3">
                <span className="text-gray-500 text-sm w-6">{i + 1}</span>
                <div className="flex-1 bg-white/5 rounded-full h-6 overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-purple-600/40 to-blue-600/40 rounded-full flex items-center px-3"
                    style={{
                      width: `${(q.count / stats.top_queries[0].count) * 100}%`,
                    }}
                  >
                    <span className="text-gray-300 text-xs truncate">{q.query}</span>
                  </div>
                </div>
                <span className="text-gray-400 text-sm w-8 text-right">{q.count}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
