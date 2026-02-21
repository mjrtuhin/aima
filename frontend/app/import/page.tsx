"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import {
  Upload,
  Search,
  CheckCircle,
  AlertTriangle,
  Loader2,
  ExternalLink,
  ArrowRight,
  Table,
  Users,
  ShoppingBag,
} from "lucide-react";

const ORG_ID = "00000000-0000-0000-0000-000000000001";

type ColumnInfo = {
  name: string;
  detected_as: string | null;
};

type PreviewResult = {
  row_count: number;
  column_count: number;
  columns: ColumnInfo[];
  mapping: Record<string, string>;
  warnings: string[];
};

type ImportResult = {
  success: boolean;
  customers_imported: number;
  orders_imported: number;
  message: string;
};

const FIELD_COLORS: Record<string, string> = {
  email:        "bg-blue-100 text-blue-700",
  full_name:    "bg-purple-100 text-purple-700",
  first_name:   "bg-purple-100 text-purple-700",
  last_name:    "bg-purple-100 text-purple-700",
  phone:        "bg-teal-100 text-teal-700",
  city:         "bg-yellow-100 text-yellow-700",
  country:      "bg-yellow-100 text-yellow-700",
  order_id:     "bg-gray-100 text-gray-700",
  order_date:   "bg-orange-100 text-orange-700",
  amount:       "bg-green-100 text-green-700",
  product_name: "bg-pink-100 text-pink-700",
  status:       "bg-indigo-100 text-indigo-700",
  quantity:     "bg-cyan-100 text-cyan-700",
  currency:     "bg-lime-100 text-lime-700",
};

export default function ImportPage() {
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [importing, setImporting] = useState(false);
  const [preview, setPreview] = useState<PreviewResult | null>(null);
  const [result, setResult] = useState<ImportResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handlePreview = async () => {
    if (!url.trim()) {
      setError("Please enter a Google Sheet URL.");
      return;
    }
    setLoading(true);
    setError(null);
    setPreview(null);
    setResult(null);
    try {
      const res = await api.post("/import/preview", {
        sheet_url: url.trim(),
        org_id: ORG_ID,
      });
      setPreview(res.data);
    } catch (err: any) {
      setError(
        err?.response?.data?.detail ||
          "Could not fetch the sheet. Make sure it is set to 'Anyone with the link can view'."
      );
    } finally {
      setLoading(false);
    }
  };

  const handleImport = async () => {
    if (!url.trim()) return;
    setImporting(true);
    setError(null);
    setResult(null);
    try {
      const res = await api.post("/import/google-sheet", {
        sheet_url: url.trim(),
        org_id: ORG_ID,
      });
      setResult(res.data);
    } catch (err: any) {
      setError(
        err?.response?.data?.detail ||
          "Import failed. Please check the sheet and try again."
      );
    } finally {
      setImporting(false);
    }
  };

  const handleReset = () => {
    setUrl("");
    setPreview(null);
    setResult(null);
    setError(null);
  };

  const detectedCount = preview
    ? preview.columns.filter((c) => c.detected_as !== null).length
    : 0;

  return (
    <div className="p-8 max-w-3xl mx-auto space-y-8">

      <div>
        <h1 className="text-2xl font-bold text-gray-900">Import Data</h1>
        <p className="text-gray-500 mt-1 text-sm">
          Paste a public Google Sheet link — AIMA will auto-detect the columns
          and import your customers and orders automatically.
        </p>
      </div>

      {!result && (
        <div className="bg-white border border-gray-200 rounded-2xl p-6 space-y-4">
          <div className="flex items-center gap-2 text-sm font-medium text-gray-700">
            <Table className="w-4 h-4 text-blue-500" />
            Google Sheet URL
          </div>

          <div className="flex gap-3">
            <input
              type="text"
              value={url}
              onChange={(e) => { setUrl(e.target.value); setPreview(null); setResult(null); setError(null); }}
              placeholder="https://docs.google.com/spreadsheets/d/..."
              className="flex-1 border border-gray-300 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <button
              onClick={handlePreview}
              disabled={loading || !url.trim()}
              className="flex items-center gap-2 px-4 py-2.5 bg-gray-900 text-white rounded-lg text-sm font-medium hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {loading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Search className="w-4 h-4" />
              )}
              {loading ? "Loading…" : "Preview Columns"}
            </button>
          </div>

          <p className="text-xs text-gray-400">
            The sheet must be set to <strong>Anyone with the link can view</strong> in Google Sheets sharing settings.
          </p>

          {error && (
            <div className="flex items-start gap-2 bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-700">
              <AlertTriangle className="w-4 h-4 mt-0.5 flex-shrink-0" />
              {error}
            </div>
          )}
        </div>
      )}

      {preview && !result && (
        <div className="bg-white border border-gray-200 rounded-2xl p-6 space-y-5">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="font-semibold text-gray-900">Column Detection</h2>
              <p className="text-xs text-gray-500 mt-0.5">
                Found {preview.row_count} rows · {preview.column_count} columns ·{" "}
                <span className="text-blue-600 font-medium">{detectedCount} auto-detected</span>
              </p>
            </div>
          </div>

          {preview.warnings.length > 0 && (
            <div className="space-y-1">
              {preview.warnings.map((w, i) => (
                <div
                  key={i}
                  className="flex items-center gap-2 text-xs text-yellow-700 bg-yellow-50 border border-yellow-200 rounded-lg px-3 py-2"
                >
                  <AlertTriangle className="w-3.5 h-3.5 flex-shrink-0" />
                  {w}
                </div>
              ))}
            </div>
          )}

          <div className="rounded-xl border border-gray-100 overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50 border-b border-gray-100">
                  <th className="text-left px-4 py-2.5 text-xs font-semibold text-gray-500 uppercase tracking-wide">
                    Column in Sheet
                  </th>
                  <th className="text-left px-4 py-2.5 text-xs font-semibold text-gray-500 uppercase tracking-wide">
                    Detected As
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {preview.columns.map((col, i) => (
                  <tr key={i} className="hover:bg-gray-50 transition-colors">
                    <td className="px-4 py-2.5 font-mono text-xs text-gray-700">
                      {col.name}
                    </td>
                    <td className="px-4 py-2.5">
                      {col.detected_as ? (
                        <span
                          className={`inline-block px-2 py-0.5 rounded-full text-xs font-medium ${
                            FIELD_COLORS[col.detected_as] ?? "bg-gray-100 text-gray-700"
                          }`}
                        >
                          {col.detected_as}
                        </span>
                      ) : (
                        <span className="text-xs text-gray-400 italic">ignored</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="flex gap-3 pt-1">
            <button
              onClick={handleImport}
              disabled={importing}
              className="flex items-center gap-2 px-5 py-2.5 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {importing ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Upload className="w-4 h-4" />
              )}
              {importing ? "Importing…" : `Import ${preview.row_count} Rows`}
            </button>
            <button
              onClick={handleReset}
              className="px-4 py-2.5 border border-gray-300 text-gray-600 rounded-lg text-sm hover:bg-gray-50 transition-colors"
            >
              Cancel
            </button>
          </div>

          {error && (
            <div className="flex items-start gap-2 bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-700">
              <AlertTriangle className="w-4 h-4 mt-0.5 flex-shrink-0" />
              {error}
            </div>
          )}
        </div>
      )}

      {result && (
        <div className="bg-white border border-gray-200 rounded-2xl p-8 text-center space-y-6">
          <div className="flex justify-center">
            <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center">
              <CheckCircle className="w-8 h-8 text-green-600" />
            </div>
          </div>

          <div>
            <h2 className="text-xl font-bold text-gray-900">Import Complete!</h2>
            <p className="text-gray-500 text-sm mt-1">{result.message}</p>
          </div>

          <div className="grid grid-cols-2 gap-4 max-w-xs mx-auto">
            <div className="bg-blue-50 rounded-xl p-4">
              <div className="flex justify-center mb-1">
                <Users className="w-5 h-5 text-blue-600" />
              </div>
              <div className="text-2xl font-bold text-blue-700">
                {result.customers_imported}
              </div>
              <div className="text-xs text-blue-500 mt-0.5">Customers</div>
            </div>
            <div className="bg-purple-50 rounded-xl p-4">
              <div className="flex justify-center mb-1">
                <ShoppingBag className="w-5 h-5 text-purple-600" />
              </div>
              <div className="text-2xl font-bold text-purple-700">
                {result.orders_imported}
              </div>
              <div className="text-xs text-purple-500 mt-0.5">Orders</div>
            </div>
          </div>

          <div className="space-y-2 text-sm text-gray-600">
            <p>Your data is now in AIMA. Here&apos;s what to do next:</p>
            <div className="flex flex-col gap-1.5 items-center">
              <a
                href="/customers"
                className="flex items-center gap-1.5 text-blue-600 hover:underline font-medium"
              >
                View imported customers <ArrowRight className="w-3.5 h-3.5" />
              </a>
              <a
                href="/segments"
                className="flex items-center gap-1.5 text-blue-600 hover:underline font-medium"
              >
                Run Re-Segment to group them with AI <ArrowRight className="w-3.5 h-3.5" />
              </a>
            </div>
          </div>

          <button
            onClick={handleReset}
            className="px-5 py-2.5 border border-gray-300 text-gray-600 rounded-lg text-sm hover:bg-gray-50 transition-colors"
          >
            Import Another Sheet
          </button>
        </div>
      )}

      <div className="bg-gray-50 border border-gray-200 rounded-2xl p-5 space-y-3">
        <h3 className="text-sm font-semibold text-gray-700">How to prepare your sheet</h3>
        <ul className="text-sm text-gray-500 space-y-1.5">
          <li className="flex items-start gap-2">
            <span className="w-4 h-4 bg-blue-600 text-white rounded-full flex items-center justify-center text-xs flex-shrink-0 mt-0.5">1</span>
            Open your sheet in Google Sheets and click <strong>Share</strong>
          </li>
          <li className="flex items-start gap-2">
            <span className="w-4 h-4 bg-blue-600 text-white rounded-full flex items-center justify-center text-xs flex-shrink-0 mt-0.5">2</span>
            Set access to <strong>Anyone with the link → Viewer</strong>
          </li>
          <li className="flex items-start gap-2">
            <span className="w-4 h-4 bg-blue-600 text-white rounded-full flex items-center justify-center text-xs flex-shrink-0 mt-0.5">3</span>
            Paste the link above — AIMA will auto-detect Email, Name, Date, Amount, etc.
          </li>
          <li className="flex items-start gap-2">
            <span className="w-4 h-4 bg-blue-600 text-white rounded-full flex items-center justify-center text-xs flex-shrink-0 mt-0.5">4</span>
            Works with Daraz, Shopify, WooCommerce, or any export — any column order
          </li>
        </ul>
        <a
          href="https://support.google.com/docs/answer/9331169"
          target="_blank"
          rel="noreferrer"
          className="inline-flex items-center gap-1 text-xs text-blue-500 hover:underline"
        >
          How to share a Google Sheet <ExternalLink className="w-3 h-3" />
        </a>
      </div>
    </div>
  );
}
