"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  LineChart,
  Line,
  Legend,
} from "recharts";
import { api } from "@/lib/api";

const ORG_ID = "00000000-0000-0000-0000-000000000001";

const STATUS_BADGE: Record<string, string> = {
  draft: "bg-gray-100 text-gray-600",
  scheduled: "bg-blue-100 text-blue-700",
  running: "bg-yellow-100 text-yellow-700",
  completed: "bg-green-100 text-green-700",
  paused: "bg-orange-100 text-orange-700",
  cancelled: "bg-red-100 text-red-600",
};

const CHANNEL_ICON: Record<string, string> = {
  email: "📧",
  sms: "💬",
  push: "🔔",
  whatsapp: "💚",
};

export default function CampaignsPage() {
  const [statusFilter, setStatusFilter] = useState<string>("");

  const { data: listData, isLoading, isError } = useQuery({
    queryKey: ["campaigns", ORG_ID, statusFilter],
    queryFn: async () => {
      const params: Record<string, string> = { org_id: ORG_ID };
      if (statusFilter) params.status = statusFilter;
      const res = await api.get("/campaigns", { params });
      return res.data;
    },
  });

  const { data: summaryData } = useQuery({
    queryKey: ["campaigns-summary", ORG_ID],
    queryFn: async () => {
      const res = await api.get("/campaigns/analytics/summary", {
        params: { org_id: ORG_ID, days: 30 },
      });
      return res.data;
    },
  });

  const campaigns = listData?.campaigns ?? [];
  const summary = summaryData ?? {};

  const completedCampaigns = campaigns.filter((c: any) => c.status === "completed");
  const accuracyData = completedCampaigns.map((c: any) => ({
    name: c.name?.slice(0, 15) ?? "Campaign",
    predicted: parseFloat((c.predicted_open_rate * 100).toFixed(1)),
    actual: parseFloat((c.actual_open_rate * 100).toFixed(1)),
  }));

  const revenueData = completedCampaigns.slice(0, 10).map((c: any) => ({
    name: c.name?.slice(0, 12) ?? "Campaign",
    predicted: parseFloat((c.predicted_revenue ?? 0).toFixed(0)),
    actual: parseFloat((c.actual_revenue ?? 0).toFixed(0)),
  }));

  return (
    <div className="p-8 space-y-8">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Campaigns</h1>
          <p className="text-gray-400 text-sm mt-1">
            AI-predicted performance vs actual results across all marketing campaigns.
          </p>
        </div>
        <button className="px-4 py-2 bg-indigo-600 text-white text-sm font-medium rounded-lg hover:bg-indigo-700 transition-colors">
          New Campaign
        </button>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: "Total Campaigns (30d)", value: summary.total_campaigns ?? 0 },
          { label: "Sent", value: summary.sent_campaigns ?? 0 },
          { label: "Avg Open Rate", value: summary.avg_open_rate ? `${(summary.avg_open_rate * 100).toFixed(1)}%` : "N/A" },
          { label: "Total Revenue", value: summary.total_revenue ? `$${summary.total_revenue.toLocaleString()}` : "N/A" },
        ].map((s) => (
          <div key={s.label} className="bg-white rounded-xl border border-gray-200 p-5">
            <p className="text-sm text-gray-500 font-medium">{s.label}</p>
            <p className="text-3xl font-bold text-gray-900 mt-1">{s.value}</p>
          </div>
        ))}
      </div>

      {revenueData.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <h2 className="text-sm font-semibold text-gray-700 mb-4">Open Rate: Predicted vs Actual</h2>
            <ResponsiveContainer width="100%" height={220}>
              <LineChart data={accuracyData}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                <YAxis unit="%" tick={{ fontSize: 11 }} />
                <Tooltip formatter={(v: number) => `${v}%`} />
                <Legend />
                <Line type="monotone" dataKey="predicted" stroke="#a78bfa" strokeDasharray="5 5" name="Predicted" />
                <Line type="monotone" dataKey="actual" stroke="#6366f1" name="Actual" />
              </LineChart>
            </ResponsiveContainer>
          </div>

          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <h2 className="text-sm font-semibold text-gray-700 mb-4">Revenue: Predicted vs Actual</h2>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={revenueData} barCategoryGap="30%">
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip formatter={(v: number) => `$${v}`} />
                <Legend />
                <Bar dataKey="predicted" fill="#a78bfa" name="Predicted" radius={[4, 4, 0, 0]} />
                <Bar dataKey="actual" fill="#6366f1" name="Actual" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      <div className="bg-white rounded-xl border border-gray-200">
        <div className="px-6 py-4 border-b border-gray-100 flex items-center gap-4">
          <h2 className="text-sm font-semibold text-gray-700 flex-1">Campaign List</h2>
          <select
            className="border border-gray-200 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            <option value="">All Statuses</option>
            <option value="draft">Draft</option>
            <option value="scheduled">Scheduled</option>
            <option value="running">Running</option>
            <option value="completed">Completed</option>
          </select>
        </div>

        {isLoading ? (
          <div className="p-8 text-center text-gray-400 text-sm">Loading campaigns...</div>
        ) : isError ? (
          <div className="p-8 text-center text-red-400 text-sm">Failed to load campaigns. Is the API running?</div>
        ) : campaigns.length === 0 ? (
          <div className="p-8 text-center text-gray-400 text-sm">No campaigns found.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50">
                <tr>
                  {["Campaign", "Channel", "Status", "Scheduled", "Pred. Open", "Actual Open", "Pred. Revenue", "Actual Revenue"].map((h) => (
                    <th key={h} className="px-4 py-3 text-left font-medium text-gray-500 text-xs uppercase tracking-wide">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {campaigns.map((c: any) => (
                  <tr key={c.id} className="hover:bg-gray-50 transition-colors">
                    <td className="px-4 py-3 font-medium text-gray-800 max-w-xs truncate">{c.name}</td>
                    <td className="px-4 py-3 text-gray-600">
                      {CHANNEL_ICON[c.channel] ?? ""} {c.channel ?? "N/A"}
                    </td>
                    <td className="px-4 py-3">
                      <span className={`text-xs px-2 py-0.5 rounded-full ${STATUS_BADGE[c.status] ?? "bg-gray-100 text-gray-600"}`}>
                        {c.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-gray-500 text-xs">
                      {c.scheduled_at ? new Date(c.scheduled_at).toLocaleDateString() : "Not set"}
                    </td>
                    <td className="px-4 py-3 text-gray-600">
                      {c.predicted_open_rate != null ? `${(c.predicted_open_rate * 100).toFixed(1)}%` : "-"}
                    </td>
                    <td className="px-4 py-3">
                      {c.actual_open_rate != null ? (
                        <span
                          className={
                            c.actual_open_rate >= (c.predicted_open_rate ?? 0)
                              ? "text-green-600 font-medium"
                              : "text-red-500"
                          }
                        >
                          {(c.actual_open_rate * 100).toFixed(1)}%
                        </span>
                      ) : (
                        <span className="text-gray-400">-</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-gray-600">
                      {c.predicted_revenue != null ? `$${c.predicted_revenue.toLocaleString()}` : "-"}
                    </td>
                    <td className="px-4 py-3">
                      {c.actual_revenue != null ? (
                        <span
                          className={
                            c.actual_revenue >= (c.predicted_revenue ?? 0)
                              ? "text-green-600 font-medium"
                              : "text-red-500"
                          }
                        >
                          ${c.actual_revenue.toLocaleString()}
                        </span>
                      ) : (
                        <span className="text-gray-400">-</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
