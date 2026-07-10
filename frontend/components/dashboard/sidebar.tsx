"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion } from "framer-motion";
import {
  Dna,
  BarChart3,
  Brain,
  FileText,
  Sparkles,
  GitBranch,
  Activity,
  Users,
  Shield,
  Settings,
  LogOut,
} from "lucide-react";

const NAV_ITEMS = [
  { icon: BarChart3, label: "Dashboard", href: "/dashboard" },
  { icon: Brain, label: "Knowledge Graph", href: "/dashboard/knowledge-graph" },
  { icon: FileText, label: "ADR Registry", href: "/dashboard/adr-registry" },
  { icon: Sparkles, label: "AI Insights", href: "/dashboard/ai-insights" },
  { icon: GitBranch, label: "Integrations", href: "/dashboard/integrations" },
  { icon: Activity, label: "Activity Feed", href: "/dashboard/activity" },
  { icon: Users, label: "Team", href: "/dashboard/team" },
  { icon: Shield, label: "Governance", href: "/dashboard/governance" },
  { icon: Settings, label: "Settings", href: "/dashboard/settings" },
];

export function Sidebar() {
  const pathname = usePathname();

  const isActive = (href: string) => {
    if (href === "/dashboard") return pathname === "/dashboard";
    return pathname.startsWith(href);
  };

  return (
    <motion.aside
      initial={{ x: -20, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      transition={{ duration: 0.5 }}
      className="fixed left-0 top-0 bottom-0 w-[240px] bg-navy-950/80 backdrop-blur-xl border-r border-white/[0.04] flex flex-col z-40"
    >
      {/* Logo */}
      <Link href="/dashboard" className="flex items-center gap-2.5 px-5 h-16 border-b border-white/[0.04] hover:bg-white/[0.02] transition-colors">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-brand-purple to-brand-indigo flex items-center justify-center shadow-lg shadow-brand-purple/20">
          <Dna className="w-4.5 h-4.5 text-white" strokeWidth={2.5} />
        </div>
        <div>
          <span className="text-sm font-bold tracking-tight text-white">
            Decision<span className="gradient-text-brand">DNA</span>
          </span>
          <div className="text-[8px] text-white/20 font-medium tracking-wider uppercase">
            AI Platform
          </div>
        </div>
      </Link>

      {/* Nav */}
      <nav className="flex-1 py-3 px-3 space-y-0.5 overflow-y-auto">
        {NAV_ITEMS.map(({ icon: Icon, label, href }) => {
          const active = isActive(href);
          return (
            <Link
              key={href}
              href={href}
              className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-[13px] font-medium transition-all duration-200
                ${
                  active
                    ? "bg-brand-purple/10 text-white border border-brand-purple/15"
                    : "text-white/35 hover:text-white/70 hover:bg-white/[0.03] border border-transparent"
                }`}
            >
              <Icon className="w-4 h-4 flex-shrink-0" strokeWidth={active ? 2 : 1.5} />
              <span>{label}</span>
              {active && (
                <div className="ml-auto w-1.5 h-1.5 rounded-full bg-brand-purple" />
              )}
            </Link>
          );
        })}
      </nav>

      {/* Bottom */}
      <div className="px-3 pb-4 space-y-1 border-t border-white/[0.04] pt-3">
        <div className="flex items-center gap-3 px-3 py-2 rounded-lg">
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-brand-purple/30 to-brand-indigo/30 flex items-center justify-center text-xs font-bold text-white border border-white/10">
            JD
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-xs font-semibold text-white/80 truncate">John Doe</p>
            <p className="text-[10px] text-white/25 truncate">Platform Engineer</p>
          </div>
          <LogOut className="w-3.5 h-3.5 text-white/20 hover:text-white/50 cursor-pointer transition-colors" />
        </div>
      </div>
    </motion.aside>
  );
}
