"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { FileText, Search, ChevronRight, X, Shield, Clock, Brain, Sparkles, ArrowRight } from "lucide-react";
import { api } from "@/lib/api";
import type { DecisionItem } from "@/lib/api";

export default function ADRRegistryPage() {
  const [decisions, setDecisions] = useState<DecisionItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [selected, setSelected] = useState<DecisionItem | null>(null);

  useEffect(() => {
    api.getDecisions().then(setDecisions).catch(() => {}).finally(() => setLoading(false));
  }, []);

  const handleSearch = async () => {
    setLoading(true);
    try {
      const data = await api.getDecisions(search || undefined);
      setDecisions(data);
    } catch {}
    setLoading(false);
  };

  const confidenceColor = (c: number) => {
    if (c >= 0.8) return "#34d399";
    if (c >= 0.5) return "#fbbf24";
    return "#f87171";
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-3">
          <FileText className="w-7 h-7 text-brand-blue" />
          ADR Registry
        </h1>
        <p className="text-sm text-white/30 mt-1">{decisions.length} architecture decisions reconstructed from your engineering evidence</p>
      </motion.div>

      {/* Search */}
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}
        className="flex gap-3">
        <div className="flex-1 flex items-center gap-2 glass-input rounded-xl px-4 py-2.5">
          <Search className="w-4 h-4 text-white/20" />
          <input type="text" value={search} onChange={(e) => setSearch(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSearch()}
            placeholder="Search decisions... (e.g. 'redis caching', 'event-driven')"
            className="bg-transparent text-sm text-white placeholder:text-white/20 outline-none flex-1" />
        </div>
        <motion.button whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }} onClick={handleSearch}
          className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-brand-purple to-brand-indigo text-white text-sm font-medium cursor-pointer shadow-lg shadow-brand-purple/15">
          Search
        </motion.button>
      </motion.div>

      {/* Loading */}
      {loading && (
        <div className="flex items-center justify-center py-20">
          <div className="w-8 h-8 border-2 border-brand-purple/30 border-t-brand-purple rounded-full animate-spin" />
        </div>
      )}

      {/* Decision list */}
      {!loading && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {decisions.slice(0, 50).map((dec, i) => (
            <motion.div key={dec.decision_id} initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.15 + i * 0.02 }} whileHover={{ y: -2 }}
              onClick={() => setSelected(dec)}
              className="glass-card rounded-2xl p-5 cursor-pointer group hover:border-brand-purple/20 transition-all">
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 rounded-lg bg-brand-blue/10 border border-brand-blue/20 flex items-center justify-center">
                    <FileText className="w-4 h-4 text-brand-blue" />
                  </div>
                  <div className="w-2 h-2 rounded-full" style={{ backgroundColor: confidenceColor(dec.confidence) }} />
                </div>
                <span className="text-[10px] font-mono text-white/20">{(dec.confidence * 100).toFixed(0)}% conf</span>
              </div>
              <h3 className="text-sm font-semibold text-white/80 group-hover:text-white transition-colors mb-2 line-clamp-2">{dec.title}</h3>
              <p className="text-[11px] text-white/30 line-clamp-2 mb-3">{dec.problem}</p>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-1.5">
                  <Brain className="w-3 h-3 text-white/20" />
                  <span className="text-[10px] text-white/20">{dec.evidence_ids.length} evidence artifacts</span>
                </div>
                <ChevronRight className="w-3.5 h-3.5 text-white/15 group-hover:text-brand-purple/60 transition-colors" />
              </div>
            </motion.div>
          ))}
        </div>
      )}

      {/* Detail drawer */}
      <AnimatePresence>
        {selected && (
          <>
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
              className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm" onClick={() => setSelected(null)} />
            <motion.div initial={{ x: "100%" }} animate={{ x: 0 }} exit={{ x: "100%" }}
              transition={{ type: "spring", damping: 25, stiffness: 300 }}
              className="fixed right-0 top-0 bottom-0 z-50 w-full max-w-2xl bg-navy-950 border-l border-white/[0.06] overflow-y-auto">
              <div className="p-8">
                <div className="flex items-center justify-between mb-6">
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full" style={{ backgroundColor: confidenceColor(selected.confidence) }} />
                    <span className="text-xs text-white/40">{(selected.confidence * 100).toFixed(0)}% confidence · {selected.evidence_ids.length} evidence artifacts</span>
                  </div>
                  <button onClick={() => setSelected(null)} className="p-2 rounded-lg hover:bg-white/[0.05] text-white/30 hover:text-white/60 transition-all cursor-pointer">
                    <X className="w-4 h-4" />
                  </button>
                </div>
                <h2 className="text-xl font-bold text-white mb-6">{selected.title}</h2>

                {[
                  { title: "Problem", content: selected.problem, icon: "🎯" },
                  { title: "Context", content: selected.context, icon: "📋" },
                  { title: "Decision", content: selected.decision, icon: "✅" },
                  { title: "Reasoning", content: selected.reasoning, icon: "💡" },
                  { title: "Alternatives", content: selected.alternatives, icon: "🔄" },
                  { title: "Implementation", content: selected.implementation, icon: "🔧" },
                  { title: "Outcomes", content: selected.outcomes, icon: "📊" },
                  { title: "Lessons Learned", content: selected.lessons, icon: "📝" },
                ].map(({ title, content, icon }) => (
                  <div key={title} className="mb-5">
                    <h4 className="text-xs font-semibold uppercase tracking-wider text-white/40 mb-2 flex items-center gap-2">
                      <span>{icon}</span> {title}
                    </h4>
                    <p className="text-sm text-white/60 leading-relaxed whitespace-pre-wrap">{content}</p>
                  </div>
                ))}
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  );
}
