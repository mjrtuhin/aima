"use client";

import { useQuery } from "@tanstack/react-query";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
  Legend,
} from "recharts";
import { api } from "@/lib/api";

const ORG_ID = "demo-org";

const CHANNEL_COLORS: Record<string, string> = {
  email: "#6366f1",
  sms: "#8b5cf6",
  paid_search: "#22d3ee",
  paid_social: "#34d399",
  organic: "#fbbf24",
  direct: "#fb923c",
  referral: "#f87171",
};

export default function AttributionPage() {
  const { data: mmmData, isLoading: mmmLoading } = useQuery({
    queryKey: ["mmm", ORG_ID],
    queryFn: async () => {
      const res = await api.get("/attribution/mmm/results", { params: { org_id: ORG_ID } });
      return res.data;
    },
  });

  const { data: channelData, isLoading: channelLoading } = useQuery({
    queryKey: ["channel-performance", ORG_ID],
    queryFn: async () => {
      const res = await api.get("/attribution/channel-performance", { params: { org_id: ORG_ID } });
      return res.data;
    },
  });

  const { data: budgetData } = useQuery({
    queryKey: ["budget-optimizer", ORG_ID],
    queryFn: async () => {
      const res = await api.get("/attribution/budget-optimizer", {
        params: { org_id: ORG_ID, total_budget: 50000 },
      });
      return res.data;
    },
  });

  const mmmChannels: any[] = mmmData?.channels ?? [];
  const channelPerfList: any[] = channelData?.channels ?? [];

  const channelContributions: Record<string, any> = Object.fromEntries(
    mmmChannels.map((ch: any) => {
      const perf = channelPerfList.find((p) => p.channel === ch.name) ?? {};
      return [
        ch.name,
        {
          contribution_pct: ch.contribution_pct ?? 0,
          attributed_revenue: perf.revenue_attributed ?? 0,
          adstock_decay: ch.adstock_decay ?? 0,
          saturation_alpha: ch.saturation_alpha ?? 0,
        },
      ];
    })
  );

  const channelRoi: Record<string, number> = Object.fromEntries(
    mmmChannels.map((ch: any) => [ch.name, ch.roi ?? 0])
  );

  const budgetAllocation: Record<string, any> = budgetData?.allocation ?? {};

  const topChannel =
    mmmChannels.length > 0
      ? mmmChannels.reduce((best: any, ch: any) =>
          (ch.contribution_pct ?? 0) > (best.contribution_pct ?? 0) ? ch : best
        ).name
      : "N/A";

  const totalAttributedRevenue = channelData?.total_revenue ?? 0;
  const r2Score = mmmData?.r_squared ?? mmmData?.r2_score ?? 0;

  const contributionBarData = Object.entries(channelContributions).map(([channel, val]: [string, any]) => ({
    channel,
    contribution: parseFloat((val.contribution_pct).toFixed(1)),
    revenue: val.attributed_revenue ?? 0,
  }));

  const roiBarData = Object.entries(channelRoi).map(([channel, roi]: [string, any]) => ({
    channel,
    roi: parseFloat((roi ?? 0).toFixed(2)),
  })).sort((a, b) => b.roi - a.roi);

  const budgetBarData = Object.entries(budgetAllocation).map(([channel, val]: [string, any]) => ({
    channel,
    current: val.current_budget ?? 0,
    recommended: val.recommended_budget ?? 0,
  }));

  return (
    <div className="p-8 space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-white">Attribution and MMM</h1>
        <p className="text-gray-400 text-sm mt-1">
          Neural Marketing Mix Model with adstock, saturation, and causal channel attribution.
        </p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: "Total Attributed Revenue", value: totalAttributedRevenue > 0 ? `$${totalAttributedRevenue.toLocaleString()}` : "N/A" },
          { label: "Top Channel", value: topChannel },
          { label: "Model R² Score", value: r2Score > 0 ? r2Score.toFixed(3) : "N/A" },
          { label: "Channels Analyzed", value: mmmChannels.length },
        ].map((s) => (
          <div key={s.label} className="bg-white rounded-xl border border-gray-200 p-5">
            <p className="text-sm text-gray-500 font-medium">{s.label}</p>
            <p className="text-3xl font-bold text-gray-900 mt-1">{s.value}</p>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h2 className="text-sm font-semibold text-gray-700 mb-4">Channel Revenue Contribution (%)</h2>
          {mmmLoading ? (
            <div className="h-64 flex items-center justify-center text-gray-400 text-sm">Loading...</div>
          ) : contributionBarData.length === 0 ? (
            <div className="h-64 flex items-center justify-center text-gray-400 text-sm">No attribution data available.</div>
          ) : (
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={contributionBarData} layout="vertical" barCategoryGap="25%">
                <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                <XAxis type="number" unit="%" tick={{ fontSize: 11 }} />
                <YAxis type="category" dataKey="channel" tick={{ fontSize: 11 }} width={80} />
                <Tooltip formatter={(v: number) => `${v}%`} />
                <Bar dataKey="contribution" radius={[0, 4, 4, 0]}>
                  {contributionBarData.map((entry, index) => (
                    <Cell key={index} fill={CHANNEL_COLORS[entry.channel] ?? "#6366f1"} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h2 className="text-sm font-semibold text-gray-700 mb-4">ROI by Channel</h2>
          {channelLoading ? (
            <div className="h-64 flex items-center justify-center text-gray-400 text-sm">Loading...</div>
          ) : roiBarData.length === 0 ? (
            <div className="h-64 flex items-center justify-center text-gray-400 text-sm">No ROI data available.</div>
          ) : (
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={roiBarData} barCategoryGap="30%">
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="channel" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip formatter={(v: number) => `${v}x ROI`} />
                <Bar dataKey="roi" radius={[4, 4, 0, 0]}>
                  {roiBarData.map((entry, index) => (
                    <Cell key={index} fill={entry.roi >= 1 ? "#34d399" : "#f87171"} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      {budgetBarData.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h2 className="text-sm font-semibold text-gray-700 mb-1">Budget Optimizer</h2>
          <p className="text-xs text-gray-400 mb-4">
            Recommended reallocation to maximize total revenue based on the saturation curves.
          </p>
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={budgetBarData} barCategoryGap="25%">
              <CartesianGrid strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey="channel" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip formatter={(v: number) => `$${v.toLocaleString()}`} />
              <Legend />
              <Bar dataKey="current" name="Current Budget" fill="#e0e7ff" radius={[4, 4, 0, 0]} />
              <Bar dataKey="recommended" name="Recommended" fill="#6366f1" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {contributionBarData.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200">
          <div className="px-6 py-4 border-b border-gray-100">
            <h2 className="text-sm font-semibold text-gray-700">Attribution Summary Table</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50">
                <tr>
                  {["Channel", "Revenue Contribution", "Attributed Revenue", "ROI", "Adstock Decay", "Saturation"].map((h) => (
                    <th key={h} className="px-4 py-3 text-left font-medium text-gray-500 text-xs uppercase tracking-wide">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {contributionBarData.map((row) => {
                  const roiVal = channelRoi[row.channel];
                  const mmmChannel = channelContributions[row.channel];
                  return (
                    <tr key={row.channel} className="hover:bg-gray-50 transition-colors">
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: CHANNEL_COLORS[row.channel] ?? "#6366f1" }} />
                          <span className="font-medium text-gray-800 capitalize">{row.channel.replace("_", " ")}</span>
                        </div>
                      </td>
                      <td className="px-4 py-3 font-semibold text-gray-700">{row.contribution}%</td>
                      <td className="px-4 py-3 text-gray-600">${(row.revenue ?? 0).toLocaleString()}</td>
                      <td className={`px-4 py-3 font-medium ${(roiVal ?? 0) >= 1 ? "text-green-600" : "text-red-500"}`}>
                        {roiVal != null ? `${roiVal.toFixed(2)}x` : "N/A"}
                      </td>
                      <td className="px-4 py-3 text-gray-500">
                        {mmmChannel?.adstock_decay != null ? mmmChannel.adstock_decay.toFixed(3) : "N/A"}
                      </td>
                      <td className="px-4 py-3 text-gray-500">
                        {mmmChannel?.saturation_alpha != null ? mmmChannel.saturation_alpha.toFixed(3) : "N/A"}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
