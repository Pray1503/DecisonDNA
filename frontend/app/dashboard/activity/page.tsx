"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Activity, GitBranch, FileText, MessageSquare, AlertTriangle, Server, ExternalLink } from "lucide-react";
import { api } from "@/lib/api";
import type { ActivityItem } from "@/lib/api";

const FILTERS = [
  { label: "All Events", value: "" },
  { label: "ADRs", value: "adr" },
  { label: "Commits", value: "commit" },
  { label: "Pull Requests", value: "pull_request" },
  { label: "Issues", value: "issue" },
  { label: "Discussions", value: "chat" },
  { label: "Incidents", value: "incident" },
  { label: "Deployments", value: "deployment" },
];

const ICONS: Record<string, React.ElementType> = {
  adr: FileText,
  commit: GitBranch,
  pull_request: GitBranch,
  issue: FileText,
  chat: MessageSquare,
  incident: AlertTriangle,
  deployment: Server,
};

const COLORS: Record<string, string> = {
  adr: "#34d399",
  commit: "#60a5fa",
  pull_request: "#a78bfa",
  issue: "#60a5fa",
  chat: "#f472b6",
  incident: "#f87171",
  deployment: "#06b6d4",
};

export default function ActivityFeedPage() {
  const [items, setItems] = useState<ActivityItem[]>([]);
  const [filter, setFilter] = useState("");
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(0);
  const limit = 30;

  useEffect(() => {
    setPage(0);
    loadItems(true);
  }, [filter]);

  const loadItems = async (reset = false) => {
    setLoading(true);
    try {
      const currentPage = reset ? 0 : page;
      const res = await api.getActivity({
        source_type: filter || undefined,
        limit,
        offset: currentPage * limit,
      });
      if (reset) {
        setItems(res.items);
      } else {
        setItems((prev) => [...prev, ...res.items]);
      }
      setPage(currentPage + 1);
    } catch {}
    setLoading(false);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-3">
          <Activity className="w-7 h-7 text-brand-purple" />
          Engineering Activity Feed
        </h1>
        <p className="text-sm text-white/30 mt-1">
          Chronological audit log of all ingested workspace events
        </p>
      </motion.div>

      {/* Filters */}
      <div className="flex gap-2 overflow-x-auto pb-2 scrollbar-none">
        {FILTERS.map((f) => (
          <button
            key={f.value}
            onClick={() => setFilter(f.value)}
            className={`px-4 py-2 rounded-xl text-xs font-semibold cursor-pointer border transition-all flex-shrink-0
              ${
                filter === f.value
                  ? "bg-brand-purple/10 text-white border-brand-purple/20"
                  : "bg-white/[0.02] text-white/40 border-white/[0.04] hover:text-white/60"
              }`}
          >
            {f.label}
          </button>
        ))}
      </div>

      {/* List */}
      <div className="glass-card rounded-2xl p-6">
        <div className="space-y-1">
          {items.map((item, i) => {
            const Icon = ICONS[item.source_type] || FileText;
            const color = COLORS[item.source_type] || "#60a5fa";
            return (
              <motion.div
                key={item.artifact_id + i}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.25 }}
                className="flex items-center justify-between p-3 rounded-xl hover:bg-white/[0.02] transition-colors group cursor-default"
              >
                <div className="flex items-center gap-3 min-w-0 flex-1">
                  <div
                    className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0"
                    style={{ backgroundColor: `${color}10`, border: `1px solid ${color}18` }}
                  >
                    <Icon className="w-4 h-4" style={{ color }} />
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="text-[13px] text-white/80 font-medium truncate group-hover:text-white transition-colors">
                      {item.title}
                    </p>
                    <p className="text-[11px] text-white/20 mt-0.5">
                      {item.author} · {item.source} · {item.timestamp ? new Date(item.timestamp).toLocaleString() : ""}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <span
                    className="text-[9px] font-semibold uppercase tracking-wider px-2 py-0.5 rounded-full"
                    style={{ color, backgroundColor: `${color}10`, border: `1px solid ${color}18` }}
                  >
                    {item.source_type.replace("_", " ")}
                  </span>
                  {item.url && (
                    <a
                      href={item.url}
                      target="_blank"
                      rel="noreferrer"
                      className="p-1 rounded-lg text-white/20 hover:text-white/60 hover:bg-white/[0.05] transition-all cursor-pointer"
                    >
                      <ExternalLink className="w-3.5 h-3.5" />
                    </a>
                  )}
                </div>
              </motion.div>
            );
          })}

          {!loading && items.length === 0 && (
            <p className="text-sm text-white/20 text-center py-12">No activity records found</p>
          )}
        </div>

        {/* Load more */}
        {!loading && items.length > 0 && (
          <div className="pt-6 border-t border-white/[0.04] text-center">
            <button
              onClick={() => loadItems(false)}
              className="px-4 py-2.5 rounded-xl bg-white/[0.02] border border-white/[0.04] text-xs font-semibold text-white/40 hover:text-white hover:bg-white/[0.05] transition-all cursor-pointer"
            >
              Load More Activities
            </button>
          </div>
        )}

        {loading && (
          <div className="flex justify-center py-6">
            <div className="w-6 h-6 border-2 border-brand-purple/30 border-t-brand-purple rounded-full animate-spin" />
          </div>
        )}
      </div>
    </div>
  );
}
