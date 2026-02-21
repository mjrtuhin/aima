"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from "recharts";
import { api } from "@/lib/api";

const ORG_ID = "demo-org";

const SEGMENT_COLORS: Record<string, string> = {
  Champions: "#6366f1",
  "Loyal Customers": "#8b5cf6",
  "Potential Loyalists": "#a78bfa",
  "New Customers": "#22d3ee",
  "Promising": "#34d399",
  "Need Attention": "#fbbf24",
  "About to Sleep": "#fb923c",
  "At Risk": "#f87171",
  "Cannot Lose Them": "#ef4444",
  Hibernating: "#94a3b8",
  Lost: "#64748b",
};

const HEALTH_BADGE: Record<string, string> = {
  Champions: "bg-indigo-100 text-indigo-800",
  "Loyal Customers": "bg-purple-100 text-purple-800",
  "Potential Loyalists": "bg-violet-100 text-violet-800",
  "New Customers": "bg-cyan-100 text-cyan-800",
  "Promising": "bg-emerald-100 text-emerald-800",
  "Need Attention": "bg-yellow-100 text-yellow-800",
  "About to Sleep": "bg-orange-100 text-orange-800",
  "At Risk": "bg-red-100 text-red-800",
  "Cannot Lose Them": "bg-rose-100 text-rose-800",
  Hibernating: "bg-slate-100 text-slate-700",
  Lost: "bg-gray-100 text-gray-600",
};

export default function SegmentsPage() {
  const queryClient = useQueryClient();

  const { data, isLoading, isError } = useQuery({
    queryKey: ["segments", ORG_ID],
    queryFn: async () => {
      const res = await api.get(`/segments?org_id=${ORG_ID}`);
      return res.data;
    },
  });

  const triggerMutation = useMutation({
    mutationFn: async () => {
      const connectorsRes = await api.get(`/connectors?org_id=${ORG_ID}&limit=1`);
      const connectorId = connectorsRes.data?.connectors?.[0]?.id ?? "demo-connector";
      return api.post(`/modules/customer-intelligence/segment`, {
        org_id: ORG_ID,
        connector_id: connectorId,
        n_segments: "auto",
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["segments"] });
    },
  });

  const segments = data?.segments ?? [];
  const totalCustomers = segments.reduce((s: number, seg: any) => s + (seg.size ?? 0), 0);

  const pieData = segments.map((seg: any) => ({
    name: seg.name,
    value: seg.size ?? 0,
    fill: SEGMENT_COLORS[seg.name] ?? "#94a3b8",
  }));

  return (
    <div className="p-8 space-y-8">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Customer Segments</h1>
          <p className="text-gray-400 text-sm mt-1">
            AI-generated behavioral clusters using UMAP + HDBSCAN on the Temporal Behavioral Transformer fingerprints.
          </p>
        </div>
        <button
          onClick={() => triggerMutation.mutate()}
          disabled={triggerMutation.isPending}
          className="px-4 py-2 bg-indigo-600 text-white text-sm font-medium rounded-lg hover:bg-indigo-700 disabled:opacity-50 transition-colors"
        >
          {triggerMutation.isPending ? "Running..." : "Re-Segment Customers"}
        </button>
      </div>

      {triggerMutation.isSuccess && (
        <div className="bg-emerald-50 border border-emerald-200 text-emerald-700 text-sm px-4 py-3 rounded-lg">
          Segmentation task queued. Results will refresh shortly.
        </div>
      )}

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <p className="text-sm text-gray-500 font-medium">Total Segments</p>
          <p className="text-3xl font-bold text-gray-900 mt-1">{segments.length}</p>
        </div>
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <p className="text-sm text-gray-500 font-medium">Segmented Customers</p>
          <p className="text-3xl font-bold text-gray-900 mt-1">{totalCustomers.toLocaleString()}</p>
        </div>
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <p className="text-sm text-gray-500 font-medium">High Value Segments</p>
          <p className="text-3xl font-bold text-gray-900 mt-1">
            {segments.filter((s: any) => ["Champions", "Loyal Customers", "Cannot Lose Them"].includes(s.name)).length}
          </p>
        </div>
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <p className="text-sm text-gray-500 font-medium">At-Risk Segments</p>
          <p className="text-3xl font-bold text-gray-900 mt-1">
            {segments.filter((s: any) => ["At Risk", "About to Sleep", "Hibernating", "Lost"].includes(s.name)).length}
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h2 className="text-sm font-semibold text-gray-700 mb-4">Segment Distribution</h2>
          {isLoading ? (
            <div className="h-64 flex items-center justify-center text-gray-400 text-sm">Loading...</div>
          ) : segments.length === 0 ? (
            <div className="h-64 flex items-center justify-center text-gray-400 text-sm">
              No segments yet. Click Re-Segment to generate.
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={280}>
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={110}
                  paddingAngle={2}
                  dataKey="value"
                >
                  {pieData.map((entry: any, index: number) => (
                    <Cell key={index} fill={entry.fill} />
                  ))}
                </Pie>
                <Tooltip formatter={(value: number) => [`${value} customers`, "Size"]} />
                <Legend iconType="circle" iconSize={8} />
              </PieChart>
            </ResponsiveContainer>
          )}
        </div>

        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h2 className="text-sm font-semibold text-gray-700 mb-4">Segment Details</h2>
          {isLoading ? (
            <div className="space-y-3">
              {[...Array(5)].map((_, i) => (
                <div key={i} className="h-10 bg-gray-100 rounded animate-pulse" />
              ))}
            </div>
          ) : isError ? (
            <div className="text-red-400 text-sm">Failed to load segments. Is the API running?</div>
          ) : segments.length === 0 ? (
            <div className="text-gray-400 text-sm">No segments available.</div>
          ) : (
            <div className="space-y-3 overflow-y-auto max-h-72 pr-1">
              {segments.map((seg: any) => {
                const pct = totalCustomers > 0 ? ((seg.size / totalCustomers) * 100).toFixed(1) : "0";
                const badgeClass = HEALTH_BADGE[seg.name] ?? "bg-gray-100 text-gray-600";
                return (
                  <div key={seg.id} className="flex items-center gap-3">
                    <div
                      className="w-3 h-3 rounded-full flex-shrink-0"
                      style={{ backgroundColor: SEGMENT_COLORS[seg.name] ?? "#94a3b8" }}
                    />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium text-gray-800 truncate">{seg.name}</span>
                        <span className={`text-xs px-2 py-0.5 rounded-full ${badgeClass}`}>{pct}%</span>
                      </div>
                      <div className="w-full bg-gray-100 h-1.5 rounded-full mt-1">
                        <div
                          className="h-1.5 rounded-full"
                          style={{
                            width: `${pct}%`,
                            backgroundColor: SEGMENT_COLORS[seg.name] ?? "#94a3b8",
                          }}
                        />
                      </div>
                    </div>
                    <span className="text-sm text-gray-500 flex-shrink-0 w-14 text-right">
                      {(seg.size ?? 0).toLocaleString()}
                    </span>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {!isLoading && segments.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200">
          <div className="px-6 py-4 border-b border-gray-100">
            <h2 className="text-sm font-semibold text-gray-700">All Segments</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50">
                <tr>
                  {["Segment", "Size", "Avg Health Score", "Drift Status", "Actions"].map((h) => (
                    <th key={h} className="px-4 py-3 text-left font-medium text-gray-500 text-xs uppercase tracking-wide">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {segments.map((seg: any) => (
                  <tr key={seg.id} className="hover:bg-gray-50 transition-colors">
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <div
                          className="w-2.5 h-2.5 rounded-full"
                          style={{ backgroundColor: SEGMENT_COLORS[seg.name] ?? "#94a3b8" }}
                        />
                        <span className="font-medium text-gray-800">{seg.name}</span>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-gray-600">{(seg.size ?? 0).toLocaleString()}</td>
                    <td className="px-4 py-3 text-gray-600">
                      {seg.avg_health_score != null
                        ? `${(seg.avg_health_score * 100).toFixed(0)}%`
                        : "N/A"}
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`text-xs px-2 py-0.5 rounded-full ${
                          seg.drift_detected
                            ? "bg-red-100 text-red-700"
                            : "bg-green-100 text-green-700"
                        }`}
                      >
                        {seg.drift_detected ? "Drift Detected" : "Stable"}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <button className="text-xs text-indigo-600 hover:underline">Create Campaign</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
