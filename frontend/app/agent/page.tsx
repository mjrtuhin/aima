"use client";

import { useState, useRef, useEffect } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

const ORG_ID = "demo-org";

interface Message {
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
  plan?: any;
}

const STARTER_PROMPTS = [
  "Build a win-back campaign for At-Risk customers this week",
  "What segments should I focus on to maximize revenue?",
  "Create an email series for new customers in the Champions segment",
  "Which channels have the best ROI this month?",
  "Alert me when churn risk exceeds 70% in Loyal Customers segment",
];

export default function AgentPage() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content: "Hello! I am the AIMA Marketing Agent. I can help you plan campaigns, analyze segments, optimize budgets, and coordinate across all 7 AI modules. What would you like to accomplish today?",
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const { data: planHistoryData } = useQuery({
    queryKey: ["agent-history", ORG_ID],
    queryFn: async () => {
      const res = await api.get("/agent/history", { params: { org_id: ORG_ID } });
      return res.data;
    },
  });

  const chatMutation = useMutation({
    mutationFn: async (message: string) => {
      const res = await api.post("/agent/chat", {
        org_id: ORG_ID,
        message,
        history: messages.slice(-10).map((m) => ({ role: m.role, content: m.content })),
      });
      return res.data;
    },
    onSuccess: (data) => {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: data.response ?? data.message ?? "Task queued.",
          timestamp: new Date(),
          plan: data.plan ?? null,
        },
      ]);
    },
    onError: () => {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "I encountered an error. Please ensure the API is running and the agent router is active.",
          timestamp: new Date(),
        },
      ]);
    },
  });

  const handleSend = () => {
    const trimmed = input.trim();
    if (!trimmed || chatMutation.isPending) return;

    setMessages((prev) => [
      ...prev,
      { role: "user", content: trimmed, timestamp: new Date() },
    ]);
    setInput("");
    chatMutation.mutate(trimmed);
  };

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const plans = planHistoryData?.plans ?? planHistoryData?.history ?? [];

  return (
    <div className="p-8 h-full flex gap-6">
      <div className="flex-1 flex flex-col min-h-0">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-white">Marketing Agent</h1>
          <p className="text-gray-400 text-sm mt-1">
            Multi-agent AI planner coordinating all 7 AIMA modules via LangGraph.
          </p>
        </div>

        <div className="flex-1 bg-white rounded-xl border border-gray-200 flex flex-col overflow-hidden">
          <div className="flex-1 overflow-y-auto p-6 space-y-4">
            {messages.map((msg, i) => (
              <div key={i} className={`flex gap-3 ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                {msg.role === "assistant" && (
                  <div className="w-8 h-8 rounded-full bg-indigo-600 flex items-center justify-center flex-shrink-0 mt-0.5">
                    <span className="text-white text-xs font-bold">AI</span>
                  </div>
                )}
                <div className={`max-w-lg ${msg.role === "user" ? "order-first" : ""}`}>
                  <div
                    className={`px-4 py-3 rounded-2xl text-sm leading-relaxed ${
                      msg.role === "user"
                        ? "bg-indigo-600 text-white rounded-tr-sm"
                        : "bg-gray-100 text-gray-800 rounded-tl-sm"
                    }`}
                  >
                    {msg.content}
                  </div>

                  {msg.plan && (
                    <div className="mt-2 bg-indigo-50 border border-indigo-100 rounded-xl p-4">
                      <p className="text-xs font-semibold text-indigo-700 mb-2">Generated Plan</p>
                      {msg.plan.campaigns?.map((campaign: any, ci: number) => (
                        <div key={ci} className="mb-2">
                          <p className="text-xs font-medium text-gray-700">{campaign.name}</p>
                          <p className="text-xs text-gray-500">{campaign.channel} - {campaign.segment}</p>
                        </div>
                      ))}
                    </div>
                  )}

                  <p className={`text-xs text-gray-400 mt-1 ${msg.role === "user" ? "text-right" : "text-left"}`}>
                    {msg.timestamp.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                  </p>
                </div>
                {msg.role === "user" && (
                  <div className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center flex-shrink-0 mt-0.5">
                    <span className="text-gray-600 text-xs font-bold">U</span>
                  </div>
                )}
              </div>
            ))}
            {chatMutation.isPending && (
              <div className="flex gap-3 justify-start">
                <div className="w-8 h-8 rounded-full bg-indigo-600 flex items-center justify-center flex-shrink-0">
                  <span className="text-white text-xs font-bold">AI</span>
                </div>
                <div className="bg-gray-100 rounded-2xl rounded-tl-sm px-4 py-3">
                  <div className="flex gap-1 items-center h-4">
                    <div className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                    <div className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                    <div className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          <div className="border-t border-gray-100 p-4">
            <div className="flex gap-2 mb-3 flex-wrap">
              {STARTER_PROMPTS.map((prompt) => (
                <button
                  key={prompt}
                  onClick={() => { setInput(prompt); }}
                  className="text-xs px-3 py-1.5 bg-indigo-50 text-indigo-600 rounded-full hover:bg-indigo-100 transition-colors"
                >
                  {prompt.slice(0, 40)}{prompt.length > 40 ? "..." : ""}
                </button>
              ))}
            </div>
            <div className="flex gap-3">
              <input
                className="flex-1 border border-gray-200 rounded-xl px-4 py-3 text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-indigo-300"
                placeholder="Ask the agent to plan a campaign, analyze segments, optimize budget..."
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleSend(); } }}
                disabled={chatMutation.isPending}
              />
              <button
                onClick={handleSend}
                disabled={chatMutation.isPending || !input.trim()}
                className="px-5 py-3 bg-indigo-600 text-white text-sm font-medium rounded-xl hover:bg-indigo-700 disabled:opacity-50 transition-colors"
              >
                Send
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="w-72 flex-shrink-0 space-y-4">
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <h2 className="text-sm font-semibold text-gray-700 mb-3">Agent Capabilities</h2>
          <ul className="space-y-2 text-xs text-gray-600">
            {[
              "Customer Intelligence (Module 1)",
              "Campaign Planning (Module 2)",
              "Content Generation (Module 3)",
              "Brand Sentiment (Module 4)",
              "Attribution MMM (Module 5)",
              "CLV/Churn Scoring (Module 6)",
              "Multi-agent Orchestration",
            ].map((cap) => (
              <li key={cap} className="flex items-center gap-2">
                <div className="w-1.5 h-1.5 rounded-full bg-indigo-400 flex-shrink-0" />
                {cap}
              </li>
            ))}
          </ul>
        </div>

        {plans.length > 0 && (
          <div className="bg-white rounded-xl border border-gray-200 p-5">
            <h2 className="text-sm font-semibold text-gray-700 mb-3">Recent Plans</h2>
            <div className="space-y-3">
              {plans.slice(0, 5).map((plan: any) => (
                <div key={plan.id} className="border border-gray-100 rounded-lg p-3">
                  <p className="text-xs font-medium text-gray-700 truncate">{plan.name ?? "Marketing Plan"}</p>
                  <p className="text-xs text-gray-400 mt-0.5">
                    {plan.campaign_count ?? 0} campaigns
                  </p>
                  <p className="text-xs text-gray-400">
                    {plan.created_at ? new Date(plan.created_at).toLocaleDateString() : ""}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="bg-indigo-50 rounded-xl border border-indigo-100 p-5">
          <h2 className="text-sm font-semibold text-indigo-800 mb-2">Pro Tips</h2>
          <ul className="space-y-2 text-xs text-indigo-700">
            <li>Ask for a full marketing plan for a specific segment</li>
            <li>Request budget optimization across channels</li>
            <li>Ask to set up automated alerts for drift or churn</li>
            <li>Request A/B test recommendations for campaigns</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
