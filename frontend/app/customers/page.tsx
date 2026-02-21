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
  ScatterChart,
  Scatter,
  ZAxis,
} from "recharts";
import { api } from "@/lib/api";

const ORG_ID = "00000000-0000-0000-0000-000000000001";

function StatCard({ label, value, sub }: { label: string; value: string | number; sub?: string }) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5">
      <p className="text-sm text-gray-500 font-medium">{label}</p>
      <p className="text-3xl font-bold text-gray-900 mt-1">{value}</p>
      {sub && <p className="text-xs text-gray-400 mt-1">{sub}</p>}
    </div>
  );
}

export default function CustomersPage() {
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(0);
  const limit = 20;

  const { data, isLoading, isError } = useQuery({
    queryKey: ["customers", ORG_ID, page, search],
    queryFn: async () => {
      const res = await api.get(`/customers`, {
        params: { org_id: ORG_ID, limit, offset: page * limit, search: search || undefined },
      });
      return res.data;
    },
  });

  const customers = data?.customers ?? [];
  const total = data?.total ?? 0;

  const healthBuckets = [
    { bucket: "0-20", count: 0 },
    { bucket: "21-40", count: 0 },
    { bucket: "41-60", count: 0 },
    { bucket: "61-80", count: 0 },
    { bucket: "81-100", count: 0 },
  ];

  customers.forEach((c: any) => {
    const h = Math.round((c.health_score ?? 0.5) * 100);
    if (h <= 20) healthBuckets[0].count++;
    else if (h <= 40) healthBuckets[1].count++;
    else if (h <= 60) healthBuckets[2].count++;
    else if (h <= 80) healthBuckets[3].count++;
    else healthBuckets[4].count++;
  });

  const avgHealth =
    customers.length > 0
      ? (customers.reduce((s: number, c: any) => s + (c.health_score ?? 0.5), 0) / customers.length * 100).toFixed(1)
      : "N/A";

  const highValue = customers.filter((c: any) => (c.health_score ?? 0) >= 0.7).length;

  return (
    <div className="p-8 space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-white">Customers</h1>
        <p className="text-gray-400 text-sm mt-1">
          Behavioral profiles and health scores across your customer base.
        </p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard label="Total Customers" value={total.toLocaleString()} />
        <StatCard label="Avg Health Score" value={`${avgHealth}%`} sub="Higher is better" />
        <StatCard label="High-Value" value={highValue} sub="Health score above 70%" />
        <StatCard label="Showing" value={`${customers.length} of ${total}`} />
      </div>

      {customers.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h2 className="text-sm font-semibold text-gray-700 mb-4">Health Score Distribution</h2>
          <ResponsiveContainer width="100%" height={180}>
            <BarChart data={healthBuckets} barCategoryGap="30%">
              <CartesianGrid strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey="bucket" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip />
              <Bar dataKey="count" fill="#6366f1" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      <div className="bg-white rounded-xl border border-gray-200">
        <div className="px-6 py-4 border-b border-gray-100 flex items-center gap-4">
          <h2 className="text-sm font-semibold text-gray-700 flex-1">Customer List</h2>
          <input
            className="border border-gray-200 rounded-lg px-3 py-1.5 text-sm w-56 focus:outline-none focus:ring-2 focus:ring-indigo-300"
            placeholder="Search by email..."
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(0); }}
          />
        </div>

        {isLoading ? (
          <div className="p-8 text-center text-gray-400 text-sm">Loading customers...</div>
        ) : isError ? (
          <div className="p-8 text-center text-red-400 text-sm">Failed to load customers. Is the API running?</div>
        ) : customers.length === 0 ? (
          <div className="p-8 text-center text-gray-400 text-sm">No customers found.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50">
                <tr>
                  {["Email", "Name", "Health Score", "Segment", "Total Orders", "LTV", "Last Active"].map((h) => (
                    <th key={h} className="px-4 py-3 text-left font-medium text-gray-500 text-xs uppercase tracking-wide">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {customers.map((c: any) => {
                  const health = Math.round((c.health_score ?? 0.5) * 100);
                  const healthColor =
                    health >= 70 ? "text-green-600" : health >= 40 ? "text-yellow-600" : "text-red-500";
                  return (
                    <tr key={c.id} className="hover:bg-gray-50 transition-colors">
                      <td className="px-4 py-3 text-gray-800 font-medium">{c.email ?? "N/A"}</td>
                      <td className="px-4 py-3 text-gray-600">
                        {[c.first_name, c.last_name].filter(Boolean).join(" ") || "Unknown"}
                      </td>
                      <td className={`px-4 py-3 font-semibold ${healthColor}`}>{health}%</td>
                      <td className="px-4 py-3">
                        <span className="inline-block bg-indigo-50 text-indigo-700 text-xs px-2 py-0.5 rounded-full">
                          {c.segment ?? "Unassigned"}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-gray-600">{c.total_orders ?? 0}</td>
                      <td className="px-4 py-3 text-gray-600">
                        ${(c.total_revenue ?? 0).toFixed(2)}
                      </td>
                      <td className="px-4 py-3 text-gray-400 text-xs">
                        {c.last_order_date ? new Date(c.last_order_date).toLocaleDateString() : "Never"}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}

        <div className="px-6 py-4 border-t border-gray-100 flex items-center justify-between text-sm text-gray-500">
          <span>
            Page {page + 1} of {Math.ceil(total / limit) || 1}
          </span>
          <div className="flex gap-2">
            <button
              className="px-3 py-1.5 rounded-lg border border-gray-200 disabled:opacity-40 hover:bg-gray-50"
              disabled={page === 0}
              onClick={() => setPage((p) => p - 1)}
            >
              Previous
            </button>
            <button
              className="px-3 py-1.5 rounded-lg border border-gray-200 disabled:opacity-40 hover:bg-gray-50"
              disabled={(page + 1) * limit >= total}
              onClick={() => setPage((p) => p + 1)}
            >
              Next
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
