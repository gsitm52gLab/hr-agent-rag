"use client";
import StatsChart from "@/components/admin/StatsChart";

export default function AdminDashboard() {
  return (
    <div>
      <h1 className="text-2xl font-bold text-white mb-6">관리자 대시보드</h1>
      <StatsChart />
    </div>
  );
}
