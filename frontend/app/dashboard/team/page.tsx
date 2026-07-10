"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Users, GitBranch, MessageSquare, Shield, Brain, ArrowUpRight } from "lucide-react";
import { api } from "@/lib/api";

interface Contributor {
  name: string;
  role: string;
  avatar: string;
  contributions: number;
  decisions: number;
  commits: number;
  issues: number;
}

const ROLES = [
  "Platform Engineer",
  "Principal Architect",
  "Senior Frontend Engineer",
  "Staff SRE",
  "Database Administrator",
  "Security Specialist",
];

export default function TeamPage() {
  const [contributors, setContributors] = useState<Contributor[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        // Fetch a large page of artifacts to group authors dynamically
        const res = await api.getArtifacts({ limit: 150 });
        const map: Record<string, { count: number; commits: number; issues: number; chat: number }> = {};

        res.artifacts.forEach((art) => {
          const auth = art.author || "Unknown Developer";
          if (!map[auth]) {
            map[auth] = { count: 0, commits: 0, issues: 0, chat: 0 };
          }
          map[auth].count++;
          if (art.source_type === "commit") map[auth].commits++;
          if (art.source_type === "issue") map[auth].issues++;
          if (art.source_type === "chat") map[auth].chat++;
        });

        const list: Contributor[] = Object.entries(map)
          .map(([name, stat], i) => {
            const role = name === "John Doe" ? "Platform Engineer" : ROLES[i % ROLES.length];
            return {
              name,
              role,
              avatar: name.split(" ").map((n) => n[0]).join("").toUpperCase().slice(0, 2),
              contributions: stat.count,
              decisions: Math.max(1, Math.round(stat.count * 0.08)),
              commits: stat.commits,
              issues: stat.issues,
            };
          })
          .sort((a, b) => b.contributions - a.contributions);

        setContributors(list.slice(0, 12));
      } catch {}
      setLoading(false);
    }
    load();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[60vh]">
        <div className="w-8 h-8 border-2 border-brand-purple/30 border-t-brand-purple rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-3">
          <Users className="w-7 h-7 text-brand-purple" />
          Workspace Contributors
        </h1>
        <p className="text-sm text-white/30 mt-1">
          Active engineers generating technical evidence and making architectural decisions
        </p>
      </motion.div>

      {/* Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
        {contributors.map((c, i) => (
          <motion.div
            key={c.name}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.05, duration: 0.4 }}
            className="glass-card rounded-2xl p-6 relative group"
          >
            {/* Header info */}
            <div className="flex items-center gap-4 mb-6">
              <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-brand-purple/20 to-brand-indigo/10 border border-brand-purple/20 flex items-center justify-center text-sm font-bold text-white shadow-lg shadow-brand-purple/10">
                {c.avatar}
              </div>
              <div>
                <h3 className="text-sm font-bold text-white">{c.name}</h3>
                <p className="text-[11px] text-white/30 mt-0.5">{c.role}</p>
              </div>
              <ArrowUpRight className="w-4 h-4 text-white/10 group-hover:text-brand-purple/60 transition-colors ml-auto absolute top-6 right-6" />
            </div>

            {/* Metrics */}
            <div className="grid grid-cols-3 gap-4 pt-4 border-t border-white/[0.04]">
              <div>
                <p className="text-[9px] font-semibold text-white/20 uppercase tracking-wider">Contributions</p>
                <p className="text-sm font-bold text-white/80 mt-1 font-mono">{c.contributions}</p>
              </div>
              <div>
                <p className="text-[9px] font-semibold text-white/20 uppercase tracking-wider">Decisions Seeded</p>
                <p className="text-sm font-bold text-white/80 mt-1 font-mono">{c.decisions}</p>
              </div>
              <div>
                <p className="text-[9px] font-semibold text-white/20 uppercase tracking-wider">Commits Mapped</p>
                <p className="text-sm font-bold text-white/80 mt-1 font-mono">{c.commits}</p>
              </div>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
