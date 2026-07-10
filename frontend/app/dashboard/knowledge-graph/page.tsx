"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Brain, GitBranch, FileText, MessageSquare, AlertTriangle, Server, Network, Zap, Database, ArrowUpRight } from "lucide-react";
import { api } from "@/lib/api";
import type { GraphSummary } from "@/lib/api";

const TYPE_COLORS: Record<string, string> = {
  adr: "#34d399", commit: "#60a5fa", pull_request: "#a78bfa", issue: "#60a5fa",
  chat: "#f472b6", incident: "#f87171", deployment: "#34d399",
};
const TYPE_ICONS: Record<string, React.ElementType> = {
  adr: FileText, commit: GitBranch, pull_request: GitBranch, issue: FileText,
  chat: MessageSquare, incident: AlertTriangle, deployment: Server,
};
const SOURCE_COLORS: Record<string, string> = {
  github: "#60a5fa", jira: "#60a5fa", slack: "#34d399", datadog: "#a78bfa", kubernetes: "#06b6d4",
};

export default function KnowledgeGraphPage() {
  const [data, setData] = useState<GraphSummary | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getGraphSummary().then(setData).catch(() => {}).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="flex items-center justify-center h-[60vh]"><div className="w-8 h-8 border-2 border-brand-purple/30 border-t-brand-purple rounded-full animate-spin" /></div>;
  if (!data) return <div className="text-center text-white/30 py-20">Failed to load graph data. Is the backend running?</div>;

  return (
    <div className="space-y-6">
      {/* Header */}
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-3">
          <Brain className="w-7 h-7 text-brand-purple" />
          Knowledge Graph
        </h1>
        <p className="text-sm text-white/30 mt-1">Explore the evidence graph connecting all engineering artifacts</p>
      </motion.div>

      {/* Stats row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: "Total Nodes", value: data.total_nodes.toLocaleString(), icon: Database, color: "#a78bfa" },
          { label: "Total Edges", value: data.total_edges.toLocaleString(), icon: Network, color: "#60a5fa" },
          { label: "Node Types", value: Object.keys(data.nodes_by_type).length.toString(), icon: Zap, color: "#34d399" },
          { label: "Edge Types", value: Object.keys(data.edges_by_type).length.toString(), icon: GitBranch, color: "#fbbf24" },
        ].map(({ label, value, icon: Icon, color }, i) => (
          <motion.div key={label} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 + i * 0.08 }}
            className="glass-card rounded-2xl p-5">
            <div className="w-9 h-9 rounded-xl flex items-center justify-center mb-3"
              style={{ backgroundColor: `${color}12`, border: `1px solid ${color}20` }}>
              <Icon className="w-4.5 h-4.5" style={{ color }} />
            </div>
            <p className="text-2xl font-bold text-white">{value}</p>
            <p className="text-xs text-white/30">{label}</p>
          </motion.div>
        ))}
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        {/* Nodes by Type */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }}
          className="glass-card rounded-2xl p-6">
          <h3 className="text-sm font-semibold text-white mb-4">Nodes by Type</h3>
          <div className="space-y-3">
            {Object.entries(data.nodes_by_type).sort((a, b) => b[1] - a[1]).map(([type, count]) => {
              const Icon = TYPE_ICONS[type] || FileText;
              const color = TYPE_COLORS[type] || "#60a5fa";
              const pct = (count / data.total_nodes) * 100;
              return (
                <div key={type} className="space-y-1">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Icon className="w-3.5 h-3.5" style={{ color }} />
                      <span className="text-xs text-white/60 capitalize">{type.replace("_", " ")}</span>
                    </div>
                    <span className="text-xs text-white/40 font-mono">{count.toLocaleString()}</span>
                  </div>
                  <div className="w-full h-1.5 bg-white/[0.04] rounded-full overflow-hidden">
                    <motion.div initial={{ width: 0 }} animate={{ width: `${pct}%` }} transition={{ delay: 0.5, duration: 0.8 }}
                      className="h-full rounded-full" style={{ backgroundColor: color }} />
                  </div>
                </div>
              );
            })}
          </div>
        </motion.div>

        {/* Nodes by Source */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.4 }}
          className="glass-card rounded-2xl p-6">
          <h3 className="text-sm font-semibold text-white mb-4">Nodes by Source</h3>
          <div className="space-y-3">
            {Object.entries(data.nodes_by_source).sort((a, b) => b[1] - a[1]).map(([source, count]) => {
              const color = SOURCE_COLORS[source] || "#60a5fa";
              const pct = (count / data.total_nodes) * 100;
              return (
                <div key={source} className="space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-white/60 capitalize">{source}</span>
                    <span className="text-xs text-white/40 font-mono">{count.toLocaleString()}</span>
                  </div>
                  <div className="w-full h-1.5 bg-white/[0.04] rounded-full overflow-hidden">
                    <motion.div initial={{ width: 0 }} animate={{ width: `${pct}%` }} transition={{ delay: 0.6, duration: 0.8 }}
                      className="h-full rounded-full" style={{ backgroundColor: color }} />
                  </div>
                </div>
              );
            })}
          </div>
        </motion.div>

        {/* Edge Types */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.5 }}
          className="glass-card rounded-2xl p-6">
          <h3 className="text-sm font-semibold text-white mb-4">Relationship Types</h3>
          <div className="space-y-2">
            {Object.entries(data.edges_by_type).sort((a, b) => b[1] - a[1]).map(([type, count]) => (
              <div key={type} className="flex items-center justify-between p-2 rounded-lg hover:bg-white/[0.02] transition-colors">
                <span className="text-xs text-white/60 font-mono">{type}</span>
                <span className="text-xs text-brand-purple/70 font-semibold">{count.toLocaleString()}</span>
              </div>
            ))}
          </div>
        </motion.div>
      </div>

      {/* Top Connected Nodes */}
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.6 }}
        className="glass-card rounded-2xl p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-semibold text-white">Most Connected Artifacts</h3>
          <span className="text-[10px] text-white/25">Hub nodes in the evidence graph</span>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {data.top_connected.map((node, i) => {
            const Icon = TYPE_ICONS[node.source_type] || FileText;
            const color = TYPE_COLORS[node.source_type] || "#60a5fa";
            return (
              <motion.div key={node.artifact_id} initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.7 + i * 0.05 }}
                className="flex items-center gap-3 p-3 rounded-xl bg-white/[0.02] border border-white/[0.04] hover:bg-white/[0.04] transition-colors cursor-pointer group">
                <div className="w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0"
                  style={{ backgroundColor: `${color}10`, border: `1px solid ${color}20` }}>
                  <Icon className="w-4 h-4" style={{ color }} />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-xs text-white/70 font-medium truncate group-hover:text-white transition-colors">{node.title}</p>
                  <p className="text-[10px] text-white/25">{node.source} · {node.source_type.replace("_", " ")}</p>
                </div>
                <div className="text-right flex-shrink-0">
                  <p className="text-sm font-bold text-brand-purple">{node.connection_count}</p>
                  <p className="text-[9px] text-white/20">edges</p>
                </div>
              </motion.div>
            );
          })}
        </div>
      </motion.div>
    </div>
  );
}
