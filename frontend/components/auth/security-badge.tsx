"use client";

import { motion } from "framer-motion";
import { Shield, Lock, KeyRound, Fingerprint } from "lucide-react";

const BADGES = [
  { icon: Shield, label: "SOC 2 Ready" },
  { icon: Lock, label: "E2E Encrypted" },
  { icon: KeyRound, label: "RBAC" },
  { icon: Fingerprint, label: "Zero Trust" },
];

export function SecurityBadge() {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ delay: 0.9, duration: 0.5 }}
      className="flex items-center justify-center gap-1.5 mt-6 flex-wrap"
    >
      <Lock className="w-3 h-3 text-brand-emerald mr-1" />
      <span className="text-[10px] font-semibold uppercase tracking-wider text-white/25 mr-2">
        Enterprise Security
      </span>
      {BADGES.map(({ icon: Icon, label }, i) => (
        <div
          key={label}
          className="flex items-center gap-1 px-2 py-0.5 rounded-full
                     bg-white/[0.02] border border-white/[0.04]
                     text-[9px] font-medium text-white/30"
        >
          <Icon className="w-2.5 h-2.5" />
          <span>{label}</span>
        </div>
      ))}
    </motion.div>
  );
}
