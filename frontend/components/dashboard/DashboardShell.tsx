"use client";

import Link from "next/link";
import { BarChart3, Bell, BookOpen, ClipboardList, FileDown, HelpCircle, Home, Search, ShieldCheck, Users } from "lucide-react";
import { DashboardMe } from "@/lib/api";

const operatorItems = [
  { href: "/dashboard", label: "Home", icon: Home },
  { href: "/dashboard/beneficiaries", label: "Beneficiaries", icon: Users },
  { href: "/dashboard/status-board", label: "Status", icon: ClipboardList },
  { href: "/dashboard/exports", label: "Exports", icon: FileDown },
  { href: "/dashboard/scheme-guide", label: "Guide", icon: BookOpen },
  { href: "/dashboard/help", label: "Training", icon: HelpCircle }
];

const adminItems = [
  { href: "/admin/analytics", label: "Analytics", icon: BarChart3 },
  { href: "/admin/unmatched-queries", label: "Zero-match", icon: Search },
  { href: "/admin/quality", label: "Quality", icon: ShieldCheck }
];

export function DashboardShell({ me, children }: { me?: DashboardMe | null; children: React.ReactNode }) {
  const role = me?.role ?? "operator";
  const items = role === "operator" ? operatorItems : [...operatorItems, ...adminItems];

  return (
    <div className="dashboardShell">
      <aside className="dashboardNav" aria-label="Dashboard navigation">
        <div>
          <p className="dashboardBrand">AdhikarAI</p>
          <p className="dashboardRole">{me?.display_name ?? "Dashboard"} · {role}</p>
        </div>
        <nav aria-label="Dashboard navigation">
          {items.map((item) => {
            const Icon = item.icon;
            return (
              <Link key={item.href} href={item.href} className="dashboardNavLink">
                <Icon size={18} aria-hidden="true" />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>
        <div className="dashboardNotice">
          <Bell size={16} aria-hidden="true" />
          <span>Cookie session only</span>
        </div>
      </aside>
      <main className="dashboardMain">{children}</main>
    </div>
  );
}
