"use client";

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { api } from "@/lib/api";

const ORG_ID = "demo-org";

const TONES = ["professional", "friendly", "urgent", "inspiring", "playful"];
const CHANNELS = ["email", "sms", "push", "whatsapp"];

interface GeneratedContent {
  subject_lines?: string[];
  preview_text?: string;
  body?: string;
  cta?: string;
  html?: string;
  message?: string;
  channel?: string;
}

export default function ContentStudioPage() {
  const [channel, setChannel] = useState("email");
  const [tone, setTone] = useState("professional");
  const [segmentName, setSegmentName] = useState("Champions");
  const [productContext, setProductContext] = useState("");
  const [activeTab, setActiveTab] = useState<"text" | "html">("text");

  const generateMutation = useMutation({
    mutationFn: async () => {
      const endpoint = channel === "email" ? "/content/generate/email" : "/content/generate/sms";
      const res = await api.post(endpoint, {
        org_id: ORG_ID,
        channel,
        tone,
        segment_type: segmentName,
        product_name: productContext || "our product",
        brand_name: "Brand",
        goal: "engagement",
      });
      return res.data as GeneratedContent;
    },
  });

  const content = generateMutation.data;

  return (
    <div className="p-8 space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Content Studio</h1>
        <p className="text-gray-500 text-sm mt-1">
          Generate brand-consistent marketing copy using the brand voice encoder and segment context.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="space-y-5">
          <div className="bg-white rounded-xl border border-gray-200 p-6 space-y-5">
            <h2 className="text-sm font-semibold text-gray-700">Generation Settings</h2>

            <div>
              <label className="block text-xs font-medium text-gray-500 mb-2">Channel</label>
              <div className="flex gap-2 flex-wrap">
                {CHANNELS.map((c) => (
                  <button
                    key={c}
                    onClick={() => setChannel(c)}
                    className={`px-3 py-1.5 rounded-lg text-sm font-medium border transition-colors ${
                      channel === c
                        ? "bg-indigo-600 text-white border-indigo-600"
                        : "bg-white text-gray-600 border-gray-200 hover:border-indigo-300"
                    }`}
                  >
                    {c.charAt(0).toUpperCase() + c.slice(1)}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-gray-500 mb-2">Brand Tone</label>
              <div className="flex gap-2 flex-wrap">
                {TONES.map((t) => (
                  <button
                    key={t}
                    onClick={() => setTone(t)}
                    className={`px-3 py-1.5 rounded-lg text-sm font-medium border transition-colors ${
                      tone === t
                        ? "bg-indigo-600 text-white border-indigo-600"
                        : "bg-white text-gray-600 border-gray-200 hover:border-indigo-300"
                    }`}
                  >
                    {t.charAt(0).toUpperCase() + t.slice(1)}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-gray-500 mb-2">Target Segment</label>
              <input
                className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300"
                value={segmentName}
                onChange={(e) => setSegmentName(e.target.value)}
                placeholder="e.g. Champions, At Risk, New Customers"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-gray-500 mb-2">
                Product / Offer Context <span className="text-gray-400">(optional)</span>
              </label>
              <textarea
                rows={3}
                className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300 resize-none"
                value={productContext}
                onChange={(e) => setProductContext(e.target.value)}
                placeholder="Describe the product, promotion, or offer to feature in the content..."
              />
            </div>

            <button
              onClick={() => generateMutation.mutate()}
              disabled={generateMutation.isPending}
              className="w-full py-2.5 bg-indigo-600 text-white text-sm font-medium rounded-lg hover:bg-indigo-700 disabled:opacity-50 transition-colors"
            >
              {generateMutation.isPending ? "Generating..." : "Generate Content"}
            </button>

            {generateMutation.isError && (
              <div className="text-red-500 text-xs">
                Generation failed. Ensure the API is running and the content router is active.
              </div>
            )}
          </div>
        </div>

        <div className="space-y-5">
          {!content && !generateMutation.isPending && (
            <div className="bg-gray-50 rounded-xl border-2 border-dashed border-gray-200 p-12 flex items-center justify-center text-gray-400 text-sm text-center">
              Configure settings on the left and click Generate to create content.
            </div>
          )}

          {generateMutation.isPending && (
            <div className="bg-white rounded-xl border border-gray-200 p-8 flex items-center justify-center">
              <div className="text-center">
                <div className="w-8 h-8 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
                <p className="text-sm text-gray-500">Generating content with brand voice model...</p>
              </div>
            </div>
          )}

          {content && channel === "email" && (
            <div className="bg-white rounded-xl border border-gray-200 space-y-0">
              <div className="px-6 py-4 border-b border-gray-100 flex items-center gap-4">
                <h2 className="text-sm font-semibold text-gray-700 flex-1">Generated Email Content</h2>
                <div className="flex gap-1">
                  <button
                    onClick={() => setActiveTab("text")}
                    className={`px-3 py-1 rounded text-xs font-medium ${activeTab === "text" ? "bg-indigo-100 text-indigo-700" : "text-gray-500 hover:text-gray-700"}`}
                  >
                    Text
                  </button>
                  <button
                    onClick={() => setActiveTab("html")}
                    className={`px-3 py-1 rounded text-xs font-medium ${activeTab === "html" ? "bg-indigo-100 text-indigo-700" : "text-gray-500 hover:text-gray-700"}`}
                  >
                    HTML
                  </button>
                </div>
              </div>
              <div className="p-6 space-y-4">
                {activeTab === "text" ? (
                  <>
                    {content.subject_lines && content.subject_lines.length > 0 && (
                      <div>
                        <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-2">Subject Lines</p>
                        {content.subject_lines.map((s, i) => (
                          <div key={i} className="flex items-center gap-2 mb-1">
                            <span className="text-xs text-gray-400">{i + 1}.</span>
                            <span className="text-sm text-gray-800">{s}</span>
                          </div>
                        ))}
                      </div>
                    )}
                    {content.preview_text && (
                      <div>
                        <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-1">Preview Text</p>
                        <p className="text-sm text-gray-700 italic">{content.preview_text}</p>
                      </div>
                    )}
                    {content.body && (
                      <div>
                        <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-1">Body Copy</p>
                        <p className="text-sm text-gray-700 whitespace-pre-line leading-relaxed">{content.body}</p>
                      </div>
                    )}
                    {(content.cta ?? (content as any).cta_text) && (
                      <div>
                        <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-1">Call to Action</p>
                        <span className="inline-block bg-indigo-600 text-white text-sm px-4 py-2 rounded-lg">
                          {content.cta ?? (content as any).cta_text}
                        </span>
                      </div>
                    )}
                  </>
                ) : (
                  <pre className="text-xs text-gray-700 bg-gray-50 rounded-lg p-4 overflow-auto max-h-96 whitespace-pre-wrap">
                    {content.html ?? "HTML not available"}
                  </pre>
                )}
              </div>
            </div>
          )}

          {content && channel !== "email" && (
            <div className="bg-white rounded-xl border border-gray-200 p-6">
              <h2 className="text-sm font-semibold text-gray-700 mb-4">Generated {channel.toUpperCase()} Message</h2>
              <p className="text-sm text-gray-700 bg-gray-50 rounded-lg p-4 whitespace-pre-line">
                {content.message ?? content.body ?? "No content returned"}
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
