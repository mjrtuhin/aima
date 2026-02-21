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
  AreaChart,
  Area,
  Cell,
  PieChart,
  Pie,
  Legend,
} from "recharts";
import { api } from "@/lib/api";

const ORG_ID = "00000000-0000-0000-0000-000000000001";

const RISK_COLOR: Record<string, string> = {
  high: "#ef4444",
  medium: "#f59e0b",
  low: "#22c55e",
};

const RISK_BADGE: Record<string, string> = {
  high: "bg-red-100 text-red-700",
  medium: "bg-yellow-100 text-yellow-700",
  low: "bg-green-100 text-green-700",
};

const INTERVENTION_LABEL: Record<string, string> = {
  immediate_winback_offer: "Win-Back Offer",
  personalized_discount: "Personalized Discount",
  engagement_campaign: "Engagement Campaign",
  loyalty_reward: "Loyalty Reward",
  standard_nurture: "Standard Nurture",
};

export default function CLVChurnPage() {
  const { data: summaryData, isLoading: summaryLoading } = useQuery({
    queryKey: ["clv-summary", ORG_ID],
    queryFn: async () => {
      const res = await api.get("/clv-churn/summary", { params: { org_id: ORG_ID } });
      return res.data;
    },
  });

  const { data: predictionsData, isLoading: predsLoading } = useQuery({
    queryKey: ["clv-predictions", ORG_ID],
    queryFn: async () => {
      const res = await api.get("/clv-churn/predictions", {
        params: { org_id: ORG_ID, limit: 50 },
      });
      return res.data;
    },
  });

  const { data: atRiskData } = useQuery({
    queryKey: ["at-risk-segments", ORG_ID],
    queryFn: async () => {
      const res = await api.get("/clv-churn/segments/at-risk", { params: { org_id: ORG_ID } });
      return res.data;
    },
  });

  const summary = summaryData ?? {};
  const predictions = predictionsData?.predictions ?? [];
  const atRiskSegments = atRiskData?.at_risk_segments ?? [];

  const riskDist = summary.risk_distribution ?? { high: 0, medium: 0, low: 0 };
  const pieData = [
    { name: "High Risk", value: riskDist.high, fill: "#ef4444" },
    { name: "Medium Risk", value: riskDist.medium, fill: "#f59e0b" },
    { name: "Low Risk", value: riskDist.low, fill: "#22c55e" },
  ];

  const interventionCounts: Record<string, number> = {};
  predictions.forEach((p: any) => {
    const label = p.recommended_intervention ?? "unknown";
    interventionCounts[label] = (interventionCounts[label] ?? 0) + 1;
  });
  const interventionData = Object.entries(interventionCounts).map(([k, v]) => ({
    intervention: INTERVENTION_LABEL[k] ?? k,
    count: v,
  }));

  const survivalCurve = predictions.slice(0, 1).map((p: any) => {
    if (!p.survival_curve) return null;
    return p.survival_curve.map((prob: number, t: number) => ({ month: t + 1, probability: parseFloat((prob * 100).toFixed(1)) }));
  }).filter(Boolean)[0] ?? [];

  return (
    <div className="p-8 space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-white">CLV and Churn Predictor</h1>
        <p className="text-gray-400 text-sm mt-1">
          Survival analysis with DeepHit-inspired architecture predicting churn probability at 30, 60, and 90 days.
        </p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: "Customers Scored", value: (summary.total_customers_scored ?? 0).toLocaleString() },
          { label: "High-Risk Customers", value: (riskDist.high ?? 0).toLocaleString() },
          { label: "Avg CLV", value: summary.clv_stats?.avg != null ? `$${summary.clv_stats.avg.toLocaleString()}` : "N/A" },
          { label: "Total Portfolio CLV", value: summary.clv_stats?.total != null ? `$${summary.clv_stats.total.toLocaleString()}` : "N/A" },
        ].map((s) => (
          <div key={s.label} className="bg-white rounded-xl border border-gray-200 p-5">
            <p className="text-sm text-gray-500 font-medium">{s.label}</p>
            <p className="text-3xl font-bold text-gray-900 mt-1">{s.value}</p>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h2 className="text-sm font-semibold text-gray-700 mb-4">Risk Distribution</h2>
          {summaryLoading ? (
            <div className="h-48 flex items-center justify-center text-gray-400 text-sm">Loading...</div>
          ) : (
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie data={pieData} cx="50%" cy="50%" innerRadius={50} outerRadius={80} paddingAngle={3} dataKey="value">
                  {pieData.map((entry, i) => <Cell key={i} fill={entry.fill} />)}
                </Pie>
                <Tooltip />
                <Legend iconType="circle" iconSize={8} />
              </PieChart>
            </ResponsiveContainer>
          )}
        </div>

        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h2 className="text-sm font-semibold text-gray-700 mb-4">Recommended Interventions</h2>
          {interventionData.length === 0 ? (
            <div className="h-48 flex items-center justify-center text-gray-400 text-sm">Load predictions first.</div>
          ) : (
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={interventionData} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                <XAxis type="number" tick={{ fontSize: 10 }} />
                <YAxis type="category" dataKey="intervention" tick={{ fontSize: 9 }} width={110} />
                <Tooltip />
                <Bar dataKey="count" fill="#6366f1" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h2 className="text-sm font-semibold text-gray-700 mb-1">Sample Survival Curve</h2>
          <p className="text-xs text-gray-400 mb-3">Retention probability over 12 months for a high-risk customer.</p>
          {survivalCurve.length === 0 ? (
            <div className="h-40 flex items-center justify-center text-gray-400 text-sm">No curve data.</div>
          ) : (
            <ResponsiveContainer width="100%" height={160}>
              <AreaChart data={survivalCurve}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="month" tick={{ fontSize: 10 }} label={{ value: "Month", position: "insideBottom", offset: -2, fontSize: 10 }} />
                <YAxis unit="%" domain={[0, 100]} tick={{ fontSize: 10 }} />
                <Tooltip formatter={(v: number) => `${v}%`} />
                <Area type="monotone" dataKey="probability" stroke="#6366f1" fill="#e0e7ff" />
              </AreaChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      {atRiskSegments.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200">
          <div className="px-6 py-4 border-b border-gray-100">
            <h2 className="text-sm font-semibold text-gray-700">At-Risk Segments</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50">
                <tr>
                  {["Segment", "Customers", "Avg Churn Probability", "At-Risk CLV"].map((h) => (
                    <th key={h} className="px-4 py-3 text-left font-medium text-gray-500 text-xs uppercase tracking-wide">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {atRiskSegments.map((seg: any) => (
                  <tr key={seg.segment_id} className="hover:bg-gray-50 transition-colors">
                    <td className="px-4 py-3 font-medium text-gray-800">{seg.segment_name}</td>
                    <td className="px-4 py-3 text-gray-600">{seg.customer_count.toLocaleString()}</td>
                    <td className="px-4 py-3">
                      <span className={`text-xs px-2 py-0.5 rounded-full ${(seg.avg_churn_probability ?? 0) >= 0.7 ? RISK_BADGE.high : (seg.avg_churn_probability ?? 0) >= 0.4 ? RISK_BADGE.medium : RISK_BADGE.low}`}>
                        {((seg.avg_churn_probability ?? 0) * 100).toFixed(1)}%
                      </span>
                    </td>
                    <td className="px-4 py-3 text-gray-600">${(seg.at_risk_clv ?? 0).toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <div className="bg-white rounded-xl border border-gray-200">
        <div className="px-6 py-4 border-b border-gray-100">
          <h2 className="text-sm font-semibold text-gray-700">Customer Churn Predictions</h2>
        </div>
        {predsLoading ? (
          <div className="p-8 text-center text-gray-400 text-sm">Loading predictions...</div>
        ) : predictions.length === 0 ? (
          <div className="p-8 text-center text-gray-400 text-sm">No predictions yet. Run scoring from the API.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50">
                <tr>
                  {["Customer", "Risk Level", "Churn 30d", "Churn 60d", "Churn 90d", "Predicted CLV", "Intervention"].map((h) => (
                    <th key={h} className="px-4 py-3 text-left font-medium text-gray-500 text-xs uppercase tracking-wide">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {predictions.slice(0, 20).map((p: any) => (
                  <tr key={p.customer_id} className="hover:bg-gray-50 transition-colors">
                    <td className="px-4 py-3 text-gray-700 text-xs font-mono">{p.email ?? p.customer_id?.slice(0, 8)}</td>
                    <td className="px-4 py-3">
                      <span className={`text-xs px-2 py-0.5 rounded-full ${RISK_BADGE[p.risk_level] ?? RISK_BADGE.low}`}>
                        {p.risk_level}
                      </span>
                    </td>
                    <td className="px-4 py-3" style={{ color: RISK_COLOR[p.risk_level] ?? "#6b7280" }}>
                      {((p.churn_probability_30d ?? 0) * 100).toFixed(1)}%
                    </td>
                    <td className="px-4 py-3 text-gray-600">{((p.churn_probability_60d ?? 0) * 100).toFixed(1)}%</td>
                    <td className="px-4 py-3 text-gray-600">{((p.churn_probability_90d ?? 0) * 100).toFixed(1)}%</td>
                    <td className="px-4 py-3 text-gray-600">${(p.predicted_clv ?? 0).toLocaleString()}</td>
                    <td className="px-4 py-3 text-xs text-indigo-600">
                      {INTERVENTION_LABEL[p.recommended_intervention] ?? p.recommended_intervention ?? "N/A"}
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
