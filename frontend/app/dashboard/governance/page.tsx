"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Shield, Brain, AlertTriangle, CheckCircle2, ChevronRight } from "lucide-react";
import { api } from "@/lib/api";
import type { DecisionItem } from "@/lib/api";

export default function GovernancePage() {
  const [decisions, setDecisions] = useState<DecisionItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getDecisions()
      .then(setDecisions)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[60vh]">
        <div className="w-8 h-8 border-2 border-brand-purple/30 border-t-brand-purple rounded-full animate-spin" />
      </div>
    );
  }

  // Calculate metrics
  const total = decisions.length;
  const lowConfidence = decisions.filter((d) => d.confidence < 0.7);
  const highConfidence = decisions.filter((d) => d.confidence >= 0.85);
  const avgConfidence = total > 0 ? decisions.reduce((acc, d) => acc + d.confidence, 0) / total : 0;
  const avgEvidence = total > 0 ? decisions.reduce((acc, d) => acc + d.evidence_ids.length, 0) / total : 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-3">
          <Shield className="w-7 h-7 text-brand-emerald" />
          Decision Governance
        </h1>
        <p className="text-sm text-white/30 mt-1">
          Review reconstructed decision integrity, verification traces, and confidence scores
        </p>
      </motion.div>

      {/* Stats grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: "Verification Status", value: "SOC 2 Ready", desc: "Governance active", icon: CheckCircle2, color: "#34d399" },
          { label: "Avg Confidence Score", value: `${(avgConfidence * 100).toFixed(1)}%`, desc: "Integrity rating", icon: Shield, color: "#a78bfa" },
          { label: "Needs Architect Review", value: lowConfidence.length.toString(), desc: "Confidence < 70%", icon: AlertTriangle, color: "#f87171" },
          { label: "Avg Evidence Density", value: avgEvidence.toFixed(1), desc: "Nodes per decision", icon: Brain, color: "#60a5fa" },
        ].map(({ label, value, desc, icon: Icon, color }, i) => (
          <motion.div
            key={label}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.08, duration: 0.4 }}
            className="glass-card rounded-2xl p-5"
          >
            <div
              className="w-10 h-10 rounded-xl flex items-center justify-center mb-3"
              style={{ backgroundColor: `${color}12`, border: `1px solid ${color}20` }}
            >
              <Icon className="w-5 h-5" style={{ color }} />
            </div>
            <p className="text-xl font-bold text-white tracking-tight">{value}</p>
            <p className="text-xs text-white/40 mt-1">{label}</p>
            <p className="text-[10px] text-white/20 mt-0.5">{desc}</p>
          </motion.div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Review list */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="lg:col-span-2 glass-card rounded-2xl p-6"
        >
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-sm font-semibold text-white">Attention Required</h3>
              <p className="text-[11px] text-white/25 mt-0.5">Reconstructed decisions with low evidence or confidence</p>
            </div>
            <span className="text-[10px] font-bold text-red-400 bg-red-400/10 border border-red-400/20 px-2 py-0.5 rounded-full">
              {lowConfidence.length} flagged
            </span>
          </div>

          <div className="space-y-1">
            {lowConfidence.slice(0, 5).map((dec) => (
              <div
                key={dec.decision_id}
                className="flex items-start justify-between p-3 rounded-xl hover:bg-white/[0.02] transition-all cursor-pointer group"
              >
                <div className="min-w-0 flex-1">
                  <h4 className="text-xs font-semibold text-white/80 group-hover:text-white truncate">
                    {dec.title}
                  </h4>
                  <p className="text-[10px] text-white/25 mt-1">
                    Evidence base: {dec.evidence_ids.length} artifacts · Score: {(dec.confidence * 100).toFixed(0)}%
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-[9px] font-semibold text-red-400 bg-red-400/5 border border-red-400/10 px-2.5 py-0.5 rounded-full">
                    Needs Seed
                  </span>
                  <ChevronRight className="w-3.5 h-3.5 text-white/10 group-hover:text-white/40" />
                </div>
              </div>
            ))}
            {lowConfidence.length === 0 && (
              <p className="text-xs text-white/20 text-center py-12">All decisions satisfy confidence standards</p>
            )}
          </div>
        </motion.div>

        {/* High confidence */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="glass-card rounded-2xl p-6"
        >
          <div className="mb-4">
            <h3 className="text-sm font-semibold text-white">Verified Traces</h3>
            <p className="text-[11px] text-white/25 mt-0.5">High-integrity architecture decisions</p>
          </div>
          <div className="space-y-3">
            {highConfidence.slice(0, 5).map((dec) => (
              <div
                key={dec.decision_id}
                className="flex items-center justify-between p-2 rounded-xl bg-white/[0.01] border border-white/[0.03]"
              >
                <span className="text-[11px] text-white/60 truncate flex-1 pr-4">{dec.title}</span>
                <span className="text-[10px] font-bold text-brand-emerald font-mono">
                  {(dec.confidence * 100).toFixed(0)}%
                </span>
              </div>
            ))}
          </div>
        </motion.div>
      </div>
    </div>
  );
}
