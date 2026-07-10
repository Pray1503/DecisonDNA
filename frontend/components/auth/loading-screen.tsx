"use client";

import { motion, AnimatePresence } from "framer-motion";
import { Check, Dna } from "lucide-react";
import type { BootStep } from "@/hooks/use-login";

interface LoadingScreenProps {
  bootSteps: BootStep[];
  currentStep: number;
}

export function LoadingScreen({ bootSteps, currentStep }: LoadingScreenProps) {
  const progress = ((bootSteps.filter((s) => s.status === "done").length) / bootSteps.length) * 100;

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 flex items-center justify-center bg-navy-950"
    >
      {/* Background glow */}
      <div
        className="absolute w-[500px] h-[500px] rounded-full"
        style={{
          background: "radial-gradient(circle, rgba(139, 92, 246, 0.15) 0%, transparent 70%)",
          left: "50%",
          top: "50%",
          transform: "translate(-50%, -50%)",
          animation: "glow-pulse 4s ease-in-out infinite",
        }}
      />

      <div className="relative z-10 w-full max-w-md px-8">
        {/* Logo */}
        <motion.div
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5 }}
          className="flex items-center justify-center gap-3 mb-10"
        >
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 8, repeat: Infinity, ease: "linear" }}
            className="w-12 h-12 rounded-2xl bg-gradient-to-br from-brand-purple to-brand-indigo flex items-center justify-center shadow-2xl shadow-brand-purple/30"
          >
            <Dna className="w-7 h-7 text-white" strokeWidth={2} />
          </motion.div>
          <span className="text-xl font-bold text-white tracking-tight">
            Decision<span className="gradient-text-brand">DNA</span> AI
          </span>
        </motion.div>

        {/* Progress bar */}
        <div className="w-full h-1 bg-white/[0.05] rounded-full mb-8 overflow-hidden">
          <motion.div
            className="h-full bg-gradient-to-r from-brand-purple to-brand-blue rounded-full"
            initial={{ width: "0%" }}
            animate={{ width: `${progress}%` }}
            transition={{ duration: 0.4, ease: "easeOut" }}
          />
        </div>

        {/* Boot steps */}
        <div className="space-y-3">
          {bootSteps.map((step, i) => (
            <motion.div
              key={step.label}
              initial={{ opacity: 0, x: -20 }}
              animate={{
                opacity: step.status === "pending" && i > currentStep + 1 ? 0 : 1,
                x: 0,
              }}
              transition={{ delay: i * 0.1, duration: 0.4 }}
              className="flex items-center gap-3"
            >
              {/* Status indicator */}
              <div className="w-5 h-5 flex items-center justify-center flex-shrink-0">
                <AnimatePresence mode="wait">
                  {step.status === "done" ? (
                    <motion.div
                      key="check"
                      initial={{ scale: 0, rotate: -45 }}
                      animate={{ scale: 1, rotate: 0 }}
                      transition={{ type: "spring", damping: 12, stiffness: 200 }}
                      className="w-5 h-5 rounded-full bg-brand-emerald/20 flex items-center justify-center"
                    >
                      <Check className="w-3 h-3 text-brand-emerald" strokeWidth={3} />
                    </motion.div>
                  ) : step.status === "active" ? (
                    <motion.div
                      key="dot"
                      className="w-2.5 h-2.5 rounded-full bg-brand-purple"
                      animate={{ scale: [1, 1.3, 1], opacity: [0.6, 1, 0.6] }}
                      transition={{ duration: 1, repeat: Infinity }}
                    />
                  ) : (
                    <div key="empty" className="w-2 h-2 rounded-full bg-white/10" />
                  )}
                </AnimatePresence>
              </div>

              {/* Label */}
              <span
                className={`text-sm font-medium transition-colors duration-300 ${
                  step.status === "done"
                    ? "text-white/60"
                    : step.status === "active"
                    ? "text-white"
                    : "text-white/20"
                }`}
              >
                {step.label}
              </span>
            </motion.div>
          ))}
        </div>

        {/* Bottom text */}
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
          className="text-center text-[11px] text-white/20 mt-10"
        >
          Initializing your organization&apos;s AI workspace...
        </motion.p>
      </div>
    </motion.div>
  );
}
