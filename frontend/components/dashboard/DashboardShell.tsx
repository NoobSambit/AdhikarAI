"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { BarChart3, Bell, BookOpen, ClipboardList, FileDown, HelpCircle, Home, LogOut, Search, ShieldCheck, Users } from "lucide-react";
import { DashboardMe, dashboardLogout, getDashboardMe } from "@/lib/api";

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
  const pathname = usePathname();
  const router = useRouter();
  const [actor, setActor] = useState<DashboardMe | null | undefined>(me);
  const [loggingOut, setLoggingOut] = useState(false);
  const isLoginRoute = pathname === "/dashboard/login";

  useEffect(() => {
    if (isLoginRoute || actor) {
      return;
    }
    let cancelled = false;
    getDashboardMe()
      .then((nextActor) => {
        if (!cancelled) {
          setActor(nextActor);
        }
      })
      .catch(() => {
        const query = window.location.search.replace(/^\?/, "");
        const next = `${pathname}${query ? `?${query}` : ""}`;
        router.replace(`/dashboard/login?next=${encodeURIComponent(next)}`);
      });
    return () => {
      cancelled = true;
    };
  }, [actor, isLoginRoute, pathname, router]);

  async function logout() {
    setLoggingOut(true);
    try {
      await dashboardLogout();
    } finally {
      router.replace("/dashboard/login");
      router.refresh();
    }
  }

  if (isLoginRoute) {
    return <>{children}</>;
  }

  if (!actor) {
    return (
      <main className="dashboardMain" role="status">
        Loading dashboard...
      </main>
    );
  }

  const role = actor.role;
  const items = role === "operator" ? operatorItems : [...operatorItems, ...adminItems];

  return (
    <div className="dashboardShell">
      <aside className="dashboardNav" aria-label="Dashboard navigation">
        <div>
          <p className="dashboardBrand">AdhikarAI</p>
          <p className="dashboardRole">{actor.display_name} · {role}</p>
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
        <button className="dashboardLogout" type="button" onClick={logout} disabled={loggingOut}>
          <LogOut size={16} aria-hidden="true" />
          <span>{loggingOut ? "Signing out..." : "Sign out"}</span>
        </button>
      </aside>
      <main className="dashboardMain">{children}</main>
    </div>
  );
}
