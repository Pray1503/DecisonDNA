"use client";

import { motion } from "framer-motion";
import {
  Dna,
  FileText,
  GitBranch,
  Server,
  AlertTriangle,
  Sparkles,
  ArrowRight,
  CheckCircle2,
} from "lucide-react";

const SUMMARY_ITEMS = [
  { icon: FileText, label: "12 new architecture decisions", color: "#a78bfa" },
  { icon: GitBranch, label: "4 Jira updates synced", color: "#60a5fa" },
  { icon: Server, label: "2 deployments tracked", color: "#34d399" },
  { icon: AlertTriangle, label: "1 production incident", color: "#f87171" },
  { icon: Sparkles, label: "AI generated 5 new recommendations", color: "#fbbf24" },
];

export function SuccessScreen() {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 flex items-center justify-center bg-navy-950"
    >
      {/* Background glow */}
      <div
        className="absolute w-[600px] h-[600px] rounded-full"
        style={{
          background: "radial-gradient(circle, rgba(16, 185, 129, 0.12) 0%, transparent 70%)",
          left: "50%",
          top: "50%",
          transform: "translate(-50%, -50%)",
        }}
      />

      <div className="relative z-10 w-full max-w-lg px-8 text-center">
        {/* Success check animation */}
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ type: "spring", damping: 10, stiffness: 150, delay: 0.1 }}
          className="w-20 h-20 rounded-3xl bg-gradient-to-br from-brand-emerald/20 to-brand-emerald/5 border border-brand-emerald/20 flex items-center justify-center mx-auto mb-8 shadow-2xl shadow-brand-emerald/10"
        >
          <motion.div
            initial={{ scale: 0, rotate: -45 }}
            animate={{ scale: 1, rotate: 0 }}
            transition={{ type: "spring", damping: 12, stiffness: 200, delay: 0.4 }}
          >
            <CheckCircle2 className="w-10 h-10 text-brand-emerald" strokeWidth={1.5} />
          </motion.div>
        </motion.div>

        {/* Welcome text */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5, duration: 0.5 }}
        >
          <p className="text-sm text-white/40 mb-1">Welcome back,</p>
          <h1 className="text-3xl font-bold text-white tracking-tight mb-1">
            John Doe
          </h1>
          <p className="text-sm text-brand-violet font-medium">Platform Engineer</p>
          <div className="flex items-center justify-center gap-2 mt-2">
            <div className="w-2 h-2 rounded-full bg-brand-emerald animate-pulse" />
            <span className="text-xs text-white/30">NovaTech Solutions</span>
          </div>
        </motion.div>

        {/* Summary cards */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.8, duration: 0.5 }}
          className="mt-8 mb-6"
        >
          <p className="text-[11px] font-semibold uppercase tracking-widest text-white/25 mb-4">
            Today&apos;s Summary
          </p>
          <div className="glass-card rounded-2xl p-5 text-left">
            <div className="space-y-3">
              {SUMMARY_ITEMS.map(({ icon: Icon, label, color }, i) => (
                <motion.div
                  key={label}
                  initial={{ opacity: 0, x: -15 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 1 + i * 0.12, duration: 0.35 }}
                  className="flex items-center gap-3"
                >
                  <div
                    className="w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0"
                    style={{ backgroundColor: `${color}15`, border: `1px solid ${color}25` }}
                  >
                    <Icon className="w-3.5 h-3.5" style={{ color }} strokeWidth={2} />
                  </div>
                  <span className="text-[13px] text-white/70">{label}</span>
                </motion.div>
              ))}
            </div>
          </div>
        </motion.div>

        {/* Redirect indicator */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1.8 }}
          className="flex items-center justify-center gap-2 text-white/20"
        >
          <div className="w-3 h-3 border-2 border-white/20 border-t-white/50 rounded-full animate-spin" />
          <span className="text-xs">Preparing your dashboard...</span>
        </motion.div>
      </div>
    </motion.div>
  );
}
