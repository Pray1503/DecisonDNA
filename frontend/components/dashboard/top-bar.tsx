"use client";

import { motion } from "framer-motion";
import { Search, Bell, Command } from "lucide-react";

export function TopBar() {
  return (
    <motion.header
      initial={{ y: -10, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.4, delay: 0.1 }}
      className="h-16 flex items-center justify-between px-8 border-b border-white/[0.04] bg-navy-950/50 backdrop-blur-xl sticky top-0 z-30"
    >
      {/* Search */}
      <div className="flex items-center gap-2 glass-input rounded-xl px-4 py-2 w-[360px]">
        <Search className="w-4 h-4 text-white/20" />
        <input
          type="text"
          placeholder="Search decisions, ADRs, insights..."
          className="bg-transparent text-sm text-white placeholder:text-white/20 outline-none flex-1"
        />
        <div className="flex items-center gap-1 px-1.5 py-0.5 rounded bg-white/[0.05] border border-white/[0.06]">
          <Command className="w-3 h-3 text-white/30" />
          <span className="text-[10px] text-white/30 font-medium">K</span>
        </div>
      </div>

      {/* Right side */}
      <div className="flex items-center gap-3">
        <button className="relative p-2 rounded-lg hover:bg-white/[0.04] transition-colors cursor-pointer">
          <Bell className="w-4.5 h-4.5 text-white/40" />
          <div className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-brand-purple border-2 border-navy-950" />
        </button>
        <div className="w-px h-6 bg-white/[0.06]" />
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-brand-emerald animate-pulse" />
          <span className="text-xs text-white/30">NovaTech Solutions</span>
        </div>
      </div>
    </motion.header>
  );
}
