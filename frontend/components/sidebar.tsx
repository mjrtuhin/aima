"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard, Users, Megaphone, PenTool,
  Eye, BarChart3, TrendingDown, Bot, Settings, Zap, Upload
} from "lucide-react";

const NAV_ITEMS = [
  { href: "/", icon: LayoutDashboard, label: "Dashboard" },
  { href: "/customers", icon: Users, label: "Customers" },
  { href: "/import", icon: Upload, label: "Import Data" },
  { href: "/campaigns", icon: Megaphone, label: "Campaigns" },
  { href: "/content-studio", icon: PenTool, label: "Content Studio" },
  { href: "/brand-monitor", icon: Eye, label: "Brand Monitor" },
  { href: "/attribution", icon: BarChart3, label: "Attribution" },
  { href: "/clv-churn", icon: TrendingDown, label: "CLV & Churn" },
  { href: "/agent", icon: Bot, label: "AI Agent" },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-60 bg-gray-900 border-r border-gray-800 flex flex-col">
      <div className="p-6 border-b border-gray-800">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
            <Zap className="w-4 h-4 text-white" />
          </div>
          <div>
            <div className="font-bold text-white text-sm">AIMA</div>
            <div className="text-gray-500 text-xs">AI Marketing Analytics</div>
          </div>
        </div>
      </div>

      <nav className="flex-1 p-4 space-y-1">
        {NAV_ITEMS.map(({ href, icon: Icon, label }) => {
          const active = pathname === href || (href !== "/" && pathname.startsWith(href));
          return (
            <Link
              key={href}
              href={href}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors ${
                active
                  ? "bg-blue-600 text-white"
                  : "text-gray-400 hover:text-white hover:bg-gray-800"
              }`}
            >
              <Icon className="w-4 h-4 flex-shrink-0" />
              {label}
            </Link>
          );
        })}
      </nav>

      <div className="p-4 border-t border-gray-800">
        <Link
          href="/settings"
          className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-gray-400 hover:text-white hover:bg-gray-800 transition-colors"
        >
          <Settings className="w-4 h-4" />
          Settings
        </Link>
        <div className="mt-3 px-3 py-2 bg-gray-800 rounded-lg">
          <div className="text-xs text-gray-500">Version 0.1.0 | Open Source</div>
          <div className="text-xs text-blue-400 mt-0.5">MIT License</div>
        </div>
      </div>
    </aside>
  );
}
