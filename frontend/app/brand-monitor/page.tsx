"use client";

import { useQuery } from "@tanstack/react-query";
import {
  RadarChart,
  Radar,
  PolarGrid,
  PolarAngleAxis,
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from "recharts";
import { api } from "@/lib/api";

const ORG_ID = "00000000-0000-0000-0000-000000000001";

const DIMENSION_LABELS: Record<string, string> = {
  quality: "Quality",
  value: "Value",
  service: "Service",
  delivery: "Delivery",
  packaging: "Packaging",
  website_ux: "Website UX",
  returns: "Returns",
  communication: "Communication",
  sustainability: "Sustainability",
  innovation: "Innovation",
  product_quality: "Product Quality",
  customer_service: "Customer Service",
  pricing: "Pricing",
  user_experience: "User Experience",
  brand_values: "Brand Values",
  reliability: "Reliability",
  overall: "Overall",
};

const SENTIMENT_COLOR: Record<string, string> = {
  positive: "text-green-600",
  neutral: "text-gray-500",
  negative: "text-red-500",
};

const SENTIMENT_BADGE: Record<string, string> = {
  positive: "bg-green-100 text-green-700",
  neutral: "bg-gray-100 text-gray-600",
  negative: "bg-red-100 text-red-600",
};

export default function BrandMonitorPage() {
  const { data: overviewData, isLoading } = useQuery({
    queryKey: ["brand-overview", ORG_ID],
    queryFn: async () => {
      const res = await api.get("/brand/sentiment/summary", {
        params: { org_id: ORG_ID, days: 7 },
      });
      return res.data;
    },
    refetchInterval: 60000,
  });

  const { data: mentionsData } = useQuery({
    queryKey: ["brand-mentions", ORG_ID],
    queryFn: async () => {
      const res = await api.get("/brand/mentions", {
        params: { org_id: ORG_ID, limit: 20 },
      });
      return res.data;
    },
  });

  const rawDimensions: Record<string, any> = overviewData?.dimensions ?? {};
  const dimensions: Record<string, { score: number; trend: string }> = Object.fromEntries(
    Object.entries(rawDimensions).map(([key, val]: [string, any]) => [
      key,
      { score: typeof val === "number" ? val : (val?.score ?? 0), trend: val?.trend ?? "stable" },
    ])
  );
  const radarData = Object.entries(dimensions).map(([key, val]) => ({
    dimension: DIMENSION_LABELS[key] ?? key,
    score: Math.round(val.score * 100),
  }));

  const trendData: any[] = overviewData?.sentiment_trend ?? [];
  const rawMentions: any[] = mentionsData?.mentions ?? [];
  const mentions = rawMentions.map((m: any) => ({
    text: m.text ?? m.content ?? "",
    sentiment: m.sentiment ?? m.sentiment_label ?? "neutral",
    source: m.source ?? "",
    dimension: m.dimension ?? (m.aspects ? Object.keys(m.aspects)[0] : undefined),
    created_at: m.created_at,
    score: m.score ?? m.sentiment_score ?? 0,
  }));

  const totalMentions: number = overviewData?.total_mentions ?? 0;
  const breakdown = overviewData?.breakdown ?? {};
  const positiveRate = totalMentions > 0 ? (breakdown.positive ?? 0) / totalMentions : 0;
  const overallScore = (overviewData?.sentiment_score ?? 0) / 100;
  const alertDimensions: string[] = Object.entries(dimensions)
    .filter(([, val]) => val.score < 0.4)
    .map(([key]) => key);

  return (
    <div className="p-8 space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-white">Brand Monitor</h1>
        <p className="text-gray-400 text-sm mt-1">
          Aspect-based sentiment analysis across 10 brand dimensions using DeBERTa.
        </p>
      </div>

      {alertDimensions.length > 0 && (
        <div className="bg-red-50 border border-red-200 rounded-xl px-5 py-4">
          <p className="text-sm font-semibold text-red-700 mb-1">Sentiment Alerts</p>
          <p className="text-sm text-red-600">
            Negative sentiment spike detected in:{" "}
            {alertDimensions.map((d: string) => DIMENSION_LABELS[d] ?? d).join(", ")}. Review recent mentions below.
          </p>
        </div>
      )}

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: "Overall Sentiment Score", value: totalMentions > 0 ? `${Math.round(overallScore * 100)}%` : "N/A" },
          { label: "Mentions Analyzed (7d)", value: totalMentions > 0 ? totalMentions.toLocaleString() : "N/A" },
          { label: "Positive Rate", value: totalMentions > 0 ? `${(positiveRate * 100).toFixed(1)}%` : "N/A" },
          { label: "Alert Dimensions", value: alertDimensions.length },
        ].map((s) => (
          <div key={s.label} className="bg-white rounded-xl border border-gray-200 p-5">
            <p className="text-sm text-gray-500 font-medium">{s.label}</p>
            <p className="text-3xl font-bold text-gray-900 mt-1">{s.value}</p>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h2 className="text-sm font-semibold text-gray-700 mb-4">Brand Dimension Radar</h2>
          {isLoading ? (
            <div className="h-64 flex items-center justify-center text-gray-400 text-sm">Loading...</div>
          ) : radarData.length === 0 ? (
            <div className="h-64 flex items-center justify-center text-gray-400 text-sm">No data yet.</div>
          ) : (
            <ResponsiveContainer width="100%" height={280}>
              <RadarChart data={radarData}>
                <PolarGrid />
                <PolarAngleAxis dataKey="dimension" tick={{ fontSize: 11 }} />
                <Radar name="Sentiment" dataKey="score" stroke="#6366f1" fill="#6366f1" fillOpacity={0.3} />
              </RadarChart>
            </ResponsiveContainer>
          )}
        </div>

        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h2 className="text-sm font-semibold text-gray-700 mb-4">Sentiment Trend (7 Days)</h2>
          {trendData.length === 0 ? (
            <div className="h-64 flex items-center justify-center text-gray-400 text-sm">No trend data yet.</div>
          ) : (
            <ResponsiveContainer width="100%" height={280}>
              <LineChart data={trendData}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                <YAxis domain={[0, 100]} tick={{ fontSize: 11 }} />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="positive" stroke="#34d399" name="Positive" strokeWidth={2} />
                <Line type="monotone" dataKey="neutral" stroke="#94a3b8" name="Neutral" strokeWidth={2} />
                <Line type="monotone" dataKey="negative" stroke="#f87171" name="Negative" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      {Object.keys(dimensions).length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h2 className="text-sm font-semibold text-gray-700 mb-4">Dimension Breakdown</h2>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            {Object.entries(dimensions).map(([key, val]) => {
              const score = Math.round(val.score * 100);
              const color = score >= 60 ? "#34d399" : score >= 40 ? "#fbbf24" : "#f87171";
              return (
                <div key={key} className="text-center">
                  <div className="relative w-16 h-16 mx-auto mb-2">
                    <svg viewBox="0 0 36 36" className="w-full h-full -rotate-90">
                      <circle cx="18" cy="18" r="15.9" fill="none" stroke="#f1f5f9" strokeWidth="3" />
                      <circle
                        cx="18" cy="18" r="15.9" fill="none"
                        stroke={color} strokeWidth="3"
                        strokeDasharray={`${score} ${100 - score}`}
                        strokeLinecap="round"
                      />
                    </svg>
                    <span className="absolute inset-0 flex items-center justify-center text-xs font-bold text-gray-800">
                      {score}
                    </span>
                  </div>
                  <p className="text-xs text-gray-600 font-medium">{DIMENSION_LABELS[key] ?? key}</p>
                  <p className={`text-xs ${val.trend === "up" ? "text-green-500" : val.trend === "down" ? "text-red-500" : "text-gray-400"}`}>
                    {val.trend === "up" ? "Improving" : val.trend === "down" ? "Declining" : "Stable"}
                  </p>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {mentions.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200">
          <div className="px-6 py-4 border-b border-gray-100">
            <h2 className="text-sm font-semibold text-gray-700">Recent Mentions</h2>
          </div>
          <div className="divide-y divide-gray-50">
            {mentions.map((m: any, i: number) => (
              <div key={i} className="px-6 py-4">
                <div className="flex items-start gap-3">
                  <span className={`text-xs px-2 py-0.5 rounded-full flex-shrink-0 mt-0.5 ${SENTIMENT_BADGE[m.sentiment] ?? "bg-gray-100 text-gray-600"}`}>
                    {m.sentiment}
                  </span>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-gray-800">{m.text}</p>
                    <div className="flex items-center gap-3 mt-1">
                      <span className="text-xs text-gray-400">{m.source}</span>
                      {m.dimension && (
                        <span className="text-xs text-indigo-500">{DIMENSION_LABELS[m.dimension] ?? m.dimension}</span>
                      )}
                      <span className="text-xs text-gray-400">
                        {m.created_at ? new Date(m.created_at).toLocaleDateString() : ""}
                      </span>
                    </div>
                  </div>
                  <span className={`text-sm font-semibold flex-shrink-0 ${SENTIMENT_COLOR[m.sentiment] ?? "text-gray-500"}`}>
                    {m.score != null ? (m.score * 100).toFixed(0) : ""}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
