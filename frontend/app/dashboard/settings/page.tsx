"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Settings, Database, Sliders, Shield, Info, RefreshCw } from "lucide-react";
import { api } from "@/lib/api";
import type { StatsResponse } from "@/lib/api";

export default function SettingsPage() {
  const [stats, setStats] = useState<StatsResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getStats()
      .then(setStats)
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

  return (
    <div className="space-y-6">
      {/* Header */}
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-3">
          <Settings className="w-7 h-7 text-white/60" />
          System Settings
        </h1>
        <p className="text-sm text-white/30 mt-1">
          Configure workspace thresholds, database pipelines, and agent permissions
        </p>
      </motion.div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left panels (Settings options) */}
        <div className="lg:col-span-2 space-y-6">
          {/* General Config */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1, duration: 0.4 }}
            className="glass-card rounded-2xl p-6 space-y-4"
          >
            <div className="flex items-center gap-2 pb-3 border-b border-white/[0.04]">
              <Sliders className="w-4.5 h-4.5 text-brand-purple" />
              <h3 className="text-sm font-semibold text-white">Reconstruction Config</h3>
            </div>
            <div className="space-y-4">
              <div>
                <label className="block text-[11px] font-semibold uppercase tracking-wider text-white/40 mb-1.5">
                  Reconstruction Confidence Threshold
                </label>
                <input
                  type="range"
                  min="50"
                  max="100"
                  defaultValue="70"
                  className="w-full h-1.5 bg-white/[0.06] rounded-lg appearance-none cursor-pointer accent-brand-purple"
                />
                <div className="flex justify-between text-[10px] text-white/20 mt-1">
                  <span>50% (Loose)</span>
                  <span>70% (Default)</span>
                  <span>100% (Strict)</span>
                </div>
              </div>
              <div>
                <label className="block text-[11px] font-semibold uppercase tracking-wider text-white/40 mb-1.5">
                  LLM Reconstruction Provider
                </label>
                <select className="glass-input w-full rounded-xl px-4 py-2.5 text-xs text-white/80 bg-navy-950/80 outline-none border border-white/[0.08]">
                  <option>Anthropic Claude 3.5 Sonnet</option>
                  <option>OpenAI GPT-4o</option>
                  <option>Gemini 1.5 Pro</option>
                </select>
              </div>
            </div>
          </motion.div>

          {/* Access */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2, duration: 0.4 }}
            className="glass-card rounded-2xl p-6 space-y-4"
          >
            <div className="flex items-center gap-2 pb-3 border-b border-white/[0.04]">
              <Shield className="w-4.5 h-4.5 text-brand-emerald" />
              <h3 className="text-sm font-semibold text-white">Security & Audit</h3>
            </div>
            <div className="space-y-3">
              <div className="flex items-center justify-between p-3 rounded-xl bg-white/[0.01] border border-white/[0.03]">
                <div>
                  <h4 className="text-xs font-semibold text-white/80">Continuous Compliance</h4>
                  <p className="text-[10px] text-white/20 mt-0.5">Auto-run compliance check on merge logs</p>
                </div>
                <input type="checkbox" defaultChecked className="w-3.5 h-3.5 accent-brand-purple" />
              </div>
              <div className="flex items-center justify-between p-3 rounded-xl bg-white/[0.01] border border-white/[0.03]">
                <div>
                  <h4 className="text-xs font-semibold text-white/80">Graph Access Permissions</h4>
                  <p className="text-[10px] text-white/20 mt-0.5">Restrict knowledge graph endpoint to workspace users</p>
                </div>
                <input type="checkbox" defaultChecked className="w-3.5 h-3.5 accent-brand-purple" />
              </div>
            </div>
          </motion.div>
        </div>

        {/* Database metadata */}
        <div className="space-y-6">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3, duration: 0.4 }}
            className="glass-card rounded-2xl p-6 space-y-4"
          >
            <div className="flex items-center gap-2 pb-3 border-b border-white/[0.04]">
              <Database className="w-4.5 h-4.5 text-brand-blue" />
              <h3 className="text-sm font-semibold text-white">Database Information</h3>
            </div>
            {stats && (
              <div className="space-y-3 font-mono text-[11px] text-white/50">
                <div className="flex justify-between">
                  <span>DB Path</span>
                  <span className="text-white/70">data/decision_memory.db</span>
                </div>
                <div className="flex justify-between">
                  <span>Database Size</span>
                  <span className="text-white/70">45.5 MB</span>
                </div>
                <div className="flex justify-between">
                  <span>Reconstructed Decisions</span>
                  <span className="text-white/70">{stats.decisions}</span>
                </div>
                <div className="flex justify-between">
                  <span>Evidence Artifacts</span>
                  <span className="text-white/70">{stats.artifacts}</span>
                </div>
                <div className="flex justify-between">
                  <span>Graph Edges</span>
                  <span className="text-white/70">{stats.relationships}</span>
                </div>
              </div>
            )}
            <div className="pt-2 flex items-start gap-2 text-[10px] text-white/25 leading-normal">
              <Info className="w-4 h-4 text-white/25 flex-shrink-0 mt-0.5" />
              <span>
                To rebuild the SQLite decision base from scratch, execute reconstruction scripts via the CLI shell tool.
              </span>
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  );
}
