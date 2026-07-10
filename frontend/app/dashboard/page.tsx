"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
  Brain,
  FileText,
  Network,
  Sparkles,
  GitBranch,
  Server,
  AlertTriangle,
  MessageSquare,
  TrendingUp,
  ChevronRight,
  CheckCircle2,
  ArrowUpRight,
  Activity,
  Calendar,
  Plus,
  BarChart3,
  Database,
} from "lucide-react";
import { api } from "@/lib/api";
import type { StatsResponse, ActivityItem as APIActivityItem } from "@/lib/api";

/* ============================================================
   TYPES
   ============================================================ */

interface StatCard {
  label: string;
  value: string;
  change: string;
  icon: React.ElementType;
  color: string;
}

/* ============================================================
   HELPERS
   ============================================================ */

const SOURCE_TYPE_ICONS: Record<string, React.ElementType> = {
  commit: GitBranch,
  pull_request: GitBranch,
  issue: FileText,
  adr: FileText,
  chat: MessageSquare,
  incident: AlertTriangle,
  deployment: Server,
};

const SOURCE_TYPE_COLORS: Record<string, string> = {
  commit: "#60a5fa",
  pull_request: "#a78bfa",
  issue: "#60a5fa",
  adr: "#34d399",
  chat: "#f472b6",
  incident: "#f87171",
  deployment: "#34d399",
};

const QUICK_ACTIONS = [
  { label: "Create ADR", icon: Plus, desc: "Start a new Architecture Decision Record" },
  { label: "Ask AI", icon: Sparkles, desc: "Query the knowledge graph" },
  { label: "View Graph", icon: Network, desc: "Explore decision relationships" },
  { label: "Run Report", icon: BarChart3, desc: "Generate decision analytics" },
];

/* ============================================================
   PAGE
   ============================================================ */

export default function DashboardPage() {
  const [stats, setStats] = useState<StatsResponse | null>(null);
  const [activity, setActivity] = useState<APIActivityItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const [statsData, activityData] = await Promise.all([
          api.getStats(),
          api.getActivity({ limit: 8 }),
        ]);
        setStats(statsData);
        setActivity(activityData.items);
      } catch (e) {
        setError("Backend unavailable. Start FastAPI on port 8000.");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const statCards: StatCard[] = stats
    ? [
        { label: "Decisions Tracked", value: stats.decisions.toLocaleString(), change: `${stats.projects} projects`, icon: Brain, color: "#a78bfa" },
        { label: "Total Artifacts", value: stats.artifacts.toLocaleString(), change: `${stats.relationships.toLocaleString()} relationships`, icon: Database, color: "#60a5fa" },
        { label: "Active ADRs", value: ((stats as Record<string, number>)["adr"] || stats.decisions || 0).toLocaleString(), change: "Architecture decisions", icon: FileText, color: "#34d399" },
        { label: "AI Recommendations", value: stats.incidents.toLocaleString(), change: `${stats.deployments} deployments`, icon: Sparkles, color: "#fbbf24" },
      ]
    : [];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[60vh]">
        <div className="text-center space-y-4">
          <div className="w-8 h-8 border-2 border-brand-purple/30 border-t-brand-purple rounded-full animate-spin mx-auto" />
          <p className="text-sm text-white/30">Loading dashboard data...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-[60vh]">
        <div className="glass-card rounded-2xl p-8 text-center max-w-md">
          <AlertTriangle className="w-10 h-10 text-amber-400 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-white mb-2">Backend Not Connected</h3>
          <p className="text-sm text-white/40 mb-4">{error}</p>
          <code className="block text-xs text-brand-purple/80 bg-brand-purple/5 border border-brand-purple/10 rounded-lg p-3 font-mono">
            uvicorn app.main:app --reload --port 8000
          </code>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Welcome header */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="flex items-center justify-between"
      >
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">
            Good afternoon, <span className="gradient-text">John</span>
          </h1>
          <p className="text-sm text-white/30 mt-1 flex items-center gap-2">
            <Calendar className="w-3.5 h-3.5" />
            {new Date().toLocaleDateString("en-US", { weekday: "long", year: "numeric", month: "long", day: "numeric" })} · NovaTech Solutions
          </p>
        </div>
        <motion.a
          href="/dashboard/ai-insights"
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-gradient-to-r from-brand-purple to-brand-indigo
                     text-white text-sm font-medium shadow-lg shadow-brand-purple/15 hover:shadow-xl hover:shadow-brand-purple/25
                     transition-shadow cursor-pointer"
        >
          <Sparkles className="w-4 h-4" />
          Ask AI Assistant
        </motion.a>
      </motion.div>

      {/* Stat cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        {statCards.map(({ label, value, change, icon: Icon, color }, i) => (
          <motion.div
            key={label}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 + i * 0.08, duration: 0.5 }}
            whileHover={{ y: -2, scale: 1.01 }}
            className="glass-card rounded-2xl p-5 cursor-default group"
          >
            <div className="flex items-start justify-between mb-3">
              <div
                className="w-10 h-10 rounded-xl flex items-center justify-center"
                style={{ backgroundColor: `${color}12`, border: `1px solid ${color}20` }}
              >
                <Icon className="w-5 h-5" style={{ color }} strokeWidth={1.8} />
              </div>
              <div className="flex items-center gap-1 px-2 py-0.5 rounded-full bg-brand-emerald/10 border border-brand-emerald/15">
                <TrendingUp className="w-3 h-3 text-brand-emerald" />
                <span className="text-[10px] font-semibold text-brand-emerald">{change}</span>
              </div>
            </div>
            <p className="text-2xl font-bold text-white tracking-tight">{value}</p>
            <p className="text-xs text-white/30 mt-0.5">{label}</p>
          </motion.div>
        ))}
      </div>

      {/* Main grid */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        {/* Activity feed */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4, duration: 0.5 }}
          className="xl:col-span-2 glass-card rounded-2xl p-6"
        >
          <div className="flex items-center justify-between mb-5">
            <div>
              <h3 className="text-sm font-semibold text-white">Recent Activity</h3>
              <p className="text-[11px] text-white/25 mt-0.5">Live from your integrations</p>
            </div>
            <a href="/dashboard/activity" className="flex items-center gap-1 text-[11px] text-brand-purple/70 hover:text-brand-purple transition-colors font-medium">
              View all <ChevronRight className="w-3 h-3" />
            </a>
          </div>
          <div className="space-y-1">
            {activity.map((item, i) => {
              const Icon = SOURCE_TYPE_ICONS[item.source_type] || FileText;
              const color = SOURCE_TYPE_COLORS[item.source_type] || "#60a5fa";
              return (
                <motion.div
                  key={item.artifact_id}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.5 + i * 0.05, duration: 0.3 }}
                  className="flex items-start gap-3 p-3 rounded-xl hover:bg-white/[0.02] transition-colors cursor-pointer group"
                >
                  <div
                    className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5"
                    style={{ backgroundColor: `${color}10`, border: `1px solid ${color}18` }}
                  >
                    <Icon className="w-4 h-4" style={{ color }} strokeWidth={1.8} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-[13px] text-white/80 font-medium truncate group-hover:text-white transition-colors">
                      {item.title}
                    </p>
                    <p className="text-[11px] text-white/25 mt-0.5">
                      {item.author} · {item.source} · {item.timestamp ? new Date(item.timestamp).toLocaleDateString() : ""}
                    </p>
                  </div>
                  <span
                    className="text-[9px] font-semibold uppercase tracking-wider px-2 py-0.5 rounded-full flex-shrink-0 mt-1"
                    style={{ color, backgroundColor: `${color}10`, border: `1px solid ${color}18` }}
                  >
                    {item.source_type.replace("_", " ")}
                  </span>
                </motion.div>
              );
            })}
            {activity.length === 0 && (
              <p className="text-sm text-white/20 text-center py-8">No activity data available</p>
            )}
          </div>
        </motion.div>

        {/* Right sidebar */}
        <div className="space-y-6">
          {/* Quick actions */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5, duration: 0.5 }}
            className="glass-card rounded-2xl p-6"
          >
            <h3 className="text-sm font-semibold text-white mb-4">Quick Actions</h3>
            <div className="grid grid-cols-2 gap-2.5">
              {QUICK_ACTIONS.map(({ label, icon: Icon, desc }) => (
                <motion.button
                  key={label}
                  whileHover={{ y: -2, scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  className="flex flex-col items-start gap-2 p-4 rounded-xl bg-white/[0.02] border border-white/[0.04]
                             hover:bg-white/[0.05] hover:border-white/[0.08] transition-all cursor-pointer group text-left"
                >
                  <Icon className="w-5 h-5 text-brand-purple/60 group-hover:text-brand-purple transition-colors" />
                  <div>
                    <p className="text-xs font-semibold text-white/70 group-hover:text-white transition-colors">{label}</p>
                    <p className="text-[10px] text-white/20 mt-0.5 leading-relaxed">{desc}</p>
                  </div>
                </motion.button>
              ))}
            </div>
          </motion.div>

          {/* Integration status */}
          {stats && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.6, duration: 0.5 }}
              className="glass-card rounded-2xl p-6"
            >
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-semibold text-white">Data Sources</h3>
                <div className="flex items-center gap-1.5">
                  <div className="w-2 h-2 rounded-full bg-brand-emerald" />
                  <span className="text-[10px] text-brand-emerald font-medium">Connected</span>
                </div>
              </div>
              <div className="space-y-2">
                {[
                  { name: "GitHub", icon: GitBranch, count: (stats.commits || 0) + (stats.prs || 0), color: "#60a5fa" },
                  { name: "Jira", icon: FileText, count: stats.jira || 0, color: "#60a5fa" },
                  { name: "Slack", icon: MessageSquare, count: stats.slack, color: "#34d399" },
                  { name: "Datadog", icon: Activity, count: stats.incidents, color: "#a78bfa" },
                  { name: "Kubernetes", icon: Server, count: stats.deployments, color: "#06b6d4" },
                ].map(({ name, icon: Icon, count, color }) => (
                  <div key={name} className="flex items-center gap-3 p-2 rounded-lg hover:bg-white/[0.02] transition-colors">
                    <div
                      className="w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0"
                      style={{ backgroundColor: `${color}10`, border: `1px solid ${color}18` }}
                    >
                      <Icon className="w-3.5 h-3.5" style={{ color }} strokeWidth={1.8} />
                    </div>
                    <span className="text-xs text-white/60 flex-1 font-medium">{name}</span>
                    <div className="flex items-center gap-1.5">
                      <CheckCircle2 className="w-3 h-3 text-brand-emerald/60" />
                      <span className="text-[10px] text-white/20">{count.toLocaleString()} items</span>
                    </div>
                  </div>
                ))}
              </div>
            </motion.div>
          )}
        </div>
      </div>
    </div>
  );
}
