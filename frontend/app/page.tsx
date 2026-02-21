"use client";

import { useQuery } from "@tanstack/react-query";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line } from "recharts";
import { Users, TrendingUp, DollarSign, AlertTriangle, Brain, Zap } from "lucide-react";
import { api } from "@/lib/api";

const MOCK_SEGMENTS = [
  { name: "Champions", count: 2340, health: 94, ltv: 1850, color: "#10b981" },
  { name: "Loyal Customers", count: 4120, health: 81, ltv: 920, color: "#3b82f6" },
  { name: "At Risk", count: 1890, health: 34, ltv: 640, color: "#ef4444" },
  { name: "Potential Loyalists", count: 3210, health: 67, ltv: 420, color: "#8b5cf6" },
  { name: "New Customers", count: 1540, health: 55, ltv: 180, color: "#f59e0b" },
  { name: "Hibernating", count: 920, health: 15, ltv: 220, color: "#6b7280" },
];

const MOCK_REVENUE = [
  { month: "Jan", predicted: 42000, actual: 38500 },
  { month: "Feb", predicted: 48000, actual: 51200 },
  { month: "Mar", predicted: 55000, actual: 53800 },
  { month: "Apr", predicted: 61000, actual: 64300 },
  { month: "May", predicted: 68000, actual: 66100 },
  { month: "Jun", predicted: 74000, actual: 0 },
];

const StatCard = ({
  title,
  value,
  subtitle,
  icon: Icon,
  trend,
  color,
}: {
  title: string;
  value: string;
  subtitle: string;
  icon: React.ElementType;
  trend?: string;
  color: string;
}) => (
  <div className="bg-gray-900 rounded-xl p-6 border border-gray-800">
    <div className="flex items-start justify-between mb-4">
      <div className={`p-2 rounded-lg ${color}`}>
        <Icon className="w-5 h-5 text-white" />
      </div>
      {trend && (
        <span className="text-green-400 text-sm font-medium">{trend}</span>
      )}
    </div>
    <div className="text-2xl font-bold text-white mb-1">{value}</div>
    <div className="text-gray-400 text-sm">{title}</div>
    <div className="text-gray-500 text-xs mt-1">{subtitle}</div>
  </div>
);

const SegmentBar = ({ segment }: { segment: (typeof MOCK_SEGMENTS)[0] }) => (
  <div className="flex items-center gap-4 py-3 border-b border-gray-800 last:border-0">
    <div className="w-32 text-sm text-gray-300 truncate">{segment.name}</div>
    <div className="flex-1 bg-gray-800 rounded-full h-2">
      <div
        className="h-2 rounded-full"
        style={{ width: `${(segment.count / 4500) * 100}%`, backgroundColor: segment.color }}
      />
    </div>
    <div className="w-16 text-right text-sm text-gray-300">{segment.count.toLocaleString()}</div>
    <div className="w-16 text-right">
      <span
        className="text-sm font-medium px-2 py-0.5 rounded-full"
        style={{ color: segment.color, backgroundColor: segment.color + "20" }}
      >
        {segment.health}
      </span>
    </div>
    <div className="w-20 text-right text-sm text-gray-400">£{segment.ltv.toLocaleString()}</div>
  </div>
);

export default function DashboardPage() {
  return (
    <div className="p-8 space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Marketing Intelligence</h1>
          <p className="text-gray-400 text-sm mt-1">Real-time overview across all modules</p>
        </div>
        <div className="flex items-center gap-2 text-xs text-gray-500 bg-gray-900 px-3 py-2 rounded-lg border border-gray-800">
          <div className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
          Live · Updated 2 min ago
        </div>
      </div>

      <div className="grid grid-cols-4 gap-4">
        <StatCard
          title="Total Customers"
          value="14,020"
          subtitle="Across all segments"
          icon={Users}
          trend="+8.2%"
          color="bg-blue-600"
        />
        <StatCard
          title="At-Risk Customers"
          value="1,890"
          subtitle="Require immediate action"
          icon={AlertTriangle}
          trend="-3.1%"
          color="bg-red-600"
        />
        <StatCard
          title="Predicted Revenue"
          value="£74,000"
          subtitle="Next 30 days (AIMA model)"
          icon={DollarSign}
          trend="+12.4%"
          color="bg-green-600"
        />
        <StatCard
          title="Avg Customer Health"
          value="61.4"
          subtitle="Platform health index (0-100)"
          icon={TrendingUp}
          trend="+2.8pts"
          color="bg-purple-600"
        />
      </div>

      <div className="grid grid-cols-5 gap-6">
        <div className="col-span-3 bg-gray-900 rounded-xl p-6 border border-gray-800">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-lg font-semibold text-white">Revenue Forecast vs Actual</h2>
              <p className="text-gray-400 text-xs mt-0.5">AIMA Campaign Performance Predictor</p>
            </div>
            <div className="flex gap-4 text-xs">
              <div className="flex items-center gap-1.5">
                <div className="w-3 h-3 rounded-full bg-blue-500" />
                <span className="text-gray-400">Predicted</span>
              </div>
              <div className="flex items-center gap-1.5">
                <div className="w-3 h-3 rounded-full bg-green-500" />
                <span className="text-gray-400">Actual</span>
              </div>
            </div>
          </div>
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={MOCK_REVENUE}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
              <XAxis dataKey="month" tick={{ fill: "#9ca3af", fontSize: 12 }} />
              <YAxis tick={{ fill: "#9ca3af", fontSize: 12 }} tickFormatter={(v) => `£${(v / 1000).toFixed(0)}k`} />
              <Tooltip
                contentStyle={{ backgroundColor: "#111827", border: "1px solid #374151", borderRadius: 8 }}
                labelStyle={{ color: "#f9fafb" }}
                formatter={(v: number) => [`£${v.toLocaleString()}`, ""]}
              />
              <Line type="monotone" dataKey="predicted" stroke="#3b82f6" strokeWidth={2} dot={false} strokeDasharray="5 5" />
              <Line type="monotone" dataKey="actual" stroke="#10b981" strokeWidth={2} dot={{ fill: "#10b981", r: 3 }} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="col-span-2 bg-gray-900 rounded-xl p-6 border border-gray-800">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-white">Customer Segments</h2>
            <div className="flex gap-3 text-xs text-gray-500">
              <span>Customers</span>
              <span>Health</span>
              <span>Avg LTV</span>
            </div>
          </div>
          <div>
            {MOCK_SEGMENTS.map((seg) => (
              <SegmentBar key={seg.name} segment={seg} />
            ))}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-4">
        {[
          { icon: Brain, title: "Customer Intelligence", desc: "2,340 Champions identified. 1,890 At-Risk need intervention.", action: "Run segmentation", color: "text-blue-400" },
          { icon: Zap, title: "Campaign Predictor", desc: "Tuesday 10am email: 28.4% predicted open rate. Change to Wednesday 9am for +4.2%.", action: "Predict campaign", color: "text-yellow-400" },
          { icon: AlertTriangle, title: "Brand Monitor", desc: "Pricing perception score dropped 8 points in 14 days. 3 influencers mentioned pricing.", action: "View alerts", color: "text-red-400" },
        ].map(({ icon: Icon, title, desc, action, color }) => (
          <div key={title} className="bg-gray-900 rounded-xl p-6 border border-gray-800">
            <div className="flex items-center gap-2 mb-3">
              <Icon className={`w-4 h-4 ${color}`} />
              <span className="font-semibold text-white text-sm">{title}</span>
            </div>
            <p className="text-gray-400 text-sm mb-4">{desc}</p>
            <button className="text-xs text-blue-400 hover:text-blue-300 font-medium">
              {action} →
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
