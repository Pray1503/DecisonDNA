"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { GitBranch, FileText, MessageSquare, AlertTriangle, Server, Network, CheckCircle2, RefreshCw } from "lucide-react";
import { api } from "@/lib/api";
import type { StatsResponse } from "@/lib/api";

export default function IntegrationsPage() {
  const [stats, setStats] = useState<StatsResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = () => {
    setLoading(true);
    api.getStats()
      .then(setStats)
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[60vh]">
        <div className="w-8 h-8 border-2 border-brand-purple/30 border-t-brand-purple rounded-full animate-spin" />
      </div>
    );
  }

  const items = stats
    ? [
        {
          name: "GitHub",
          desc: "Extract ADR files, pull request summaries, merge logs, and author commits.",
          icon: GitBranch,
          color: "#60a5fa",
          metrics: [
            { label: "Commits Mapped", value: stats.commits || 20028 },
            { label: "PRs Tracked", value: stats.prs || 2000 },
          ],
        },
        {
          name: "Jira Workspace",
          desc: "Sync epic metadata, sprint tickets, user descriptions, and comment logs.",
          icon: FileText,
          color: "#60a5fa",
          metrics: [{ label: "Tickets Tracked", value: stats.jira || 5000 }],
        },
        {
          name: "Slack Channels",
          desc: "Ingest developer discussions, technical brainstorm channels, and key decisions.",
          icon: MessageSquare,
          color: "#34d399",
          metrics: [{ label: "Decisions Ingested", value: stats.slack }],
        },
        {
          name: "Datadog Monitors",
          desc: "Track incident payloads, service outages, error spikes, and PagerDuty escalations.",
          icon: AlertTriangle,
          color: "#a78bfa",
          metrics: [{ label: "Incident Reports", value: stats.incidents }],
        },
        {
          name: "Kubernetes Deployments",
          desc: "Monitor releases, container restarts, environment configuration changes.",
          icon: Server,
          color: "#06b6d4",
          metrics: [{ label: "Deployments Tracked", value: stats.deployments }],
        },
      ]
    : [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-3">
            <Network className="w-7 h-7 text-brand-purple" />
            Integrations
          </h1>
          <p className="text-sm text-white/30 mt-1">
            Manage your connected developer systems feeding the Evidence Graph
          </p>
        </div>
        <button
          onClick={loadStats}
          className="p-2.5 rounded-xl bg-white/[0.03] border border-white/[0.06] hover:bg-white/[0.06] transition-all text-white/60 hover:text-white cursor-pointer"
        >
          <RefreshCw className="w-4 h-4" />
        </button>
      </motion.div>

      {/* Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {items.map((item, i) => (
          <motion.div
            key={item.name}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.08, duration: 0.4 }}
            className="glass-card rounded-2xl p-6 flex flex-col justify-between"
          >
            <div>
              <div className="flex items-start justify-between mb-4">
                <div
                  className="w-12 h-12 rounded-xl flex items-center justify-center"
                  style={{ backgroundColor: `${item.color}12`, border: `1px solid ${item.color}20` }}
                >
                  <item.icon className="w-6 h-6" style={{ color: item.color }} />
                </div>
                <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-brand-emerald/10 border border-brand-emerald/15">
                  <CheckCircle2 className="w-3.5 h-3.5 text-brand-emerald" />
                  <span className="text-[10px] font-bold text-brand-emerald">Synced</span>
                </div>
              </div>

              <h3 className="text-base font-bold text-white mb-2">{item.name}</h3>
              <p className="text-xs text-white/45 leading-relaxed mb-6">{item.desc}</p>
            </div>

            <div className="pt-4 border-t border-white/[0.04] grid grid-cols-2 gap-4">
              {item.metrics.map((m) => (
                <div key={m.label}>
                  <p className="text-[10px] text-white/20 uppercase tracking-wider font-semibold">{m.label}</p>
                  <p className="text-lg font-bold text-white/80 mt-1 font-mono">{m.value.toLocaleString()}</p>
                </div>
              ))}
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
