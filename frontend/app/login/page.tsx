"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { Dna, Brain, BarChart3, Zap } from "lucide-react";
import { BackgroundAnimation } from "@/components/auth/background-animation";
import { LoginCard } from "@/components/auth/login-card";
import { LoadingScreen } from "@/components/auth/loading-screen";
import { SuccessScreen } from "@/components/auth/success-screen";
import { useLogin } from "@/hooks/use-login";

const VALUE_CARDS = [
  {
    emoji: "🧠",
    icon: Brain,
    title: "Persistent AI Memory",
    description: "Our AI remembers every important organizational decision.",
    color: "#a78bfa",
  },
  {
    emoji: "📈",
    icon: BarChart3,
    title: "Decision Intelligence",
    description: "Transform historical decisions into future recommendations.",
    color: "#60a5fa",
  },
  {
    emoji: "⚡",
    icon: Zap,
    title: "Living Knowledge",
    description: "Continuously learning from GitHub, Jira, deployments and incidents.",
    color: "#34d399",
  },
];

export default function LoginPage() {
  const router = useRouter();
  const {
    state,
    form,
    errors,
    bootSteps,
    currentBootStep,
    updateField,
    handleSubmit,
  } = useLogin();

  // Navigate to dashboard when login flow completes
  useEffect(() => {
    if (state === "redirect") {
      router.push("/dashboard");
    }
  }, [state, router]);

  return (
    <>
      {/* Boot sequence overlay */}
      <AnimatePresence mode="wait">
        {state === "booting" && (
          <LoadingScreen bootSteps={bootSteps} currentStep={currentBootStep} />
        )}
        {(state === "success" || state === "redirect") && <SuccessScreen />}
      </AnimatePresence>

      {/* Main login layout */}
      <div className="min-h-screen flex bg-navy-950 text-white overflow-hidden">
        {/* ================================
            LEFT PANEL — Branding + Illustration
            ================================ */}
        <motion.div
          initial={{ opacity: 0, x: -40 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
          className="hidden lg:flex lg:w-[55%] xl:w-[58%] relative flex-col justify-between p-10 xl:p-14"
        >
          <BackgroundAnimation />

          {/* Content layer */}
          <div className="relative z-10 flex flex-col justify-between h-full">
            {/* Top: Logo */}
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2, duration: 0.5 }}
              className="flex items-center gap-3"
            >
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-brand-purple to-brand-indigo flex items-center justify-center shadow-lg shadow-brand-purple/20">
                <Dna className="w-6 h-6 text-white" strokeWidth={2.5} />
              </div>
              <div>
                <span className="text-lg font-bold tracking-tight">
                  Decision<span className="gradient-text-brand">DNA</span> AI
                </span>
                <div className="text-[10px] text-white/25 font-medium tracking-wide uppercase">
                  Enterprise Decision Intelligence
                </div>
              </div>
            </motion.div>

            {/* Center: Headline */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4, duration: 0.6 }}
              className="max-w-lg"
            >
              <h2 className="text-4xl xl:text-5xl font-bold leading-[1.15] tracking-tight mb-4">
                Transforming{" "}
                <span className="gradient-text">Organizational Decisions</span>{" "}
                into Living Intelligence.
              </h2>
              <p className="text-base text-white/35 leading-relaxed max-w-md">
                Every decision today becomes intelligence for tomorrow. Connect your
                engineering ecosystem and let AI reconstruct the DNA of every choice
                your team makes.
              </p>
            </motion.div>

            {/* Bottom: Value cards */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.6, duration: 0.5 }}
              className="grid grid-cols-3 gap-3"
            >
              {VALUE_CARDS.map(({ emoji, title, description, color }, i) => (
                <motion.div
                  key={title}
                  initial={{ opacity: 0, y: 15 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.7 + i * 0.1, duration: 0.4 }}
                  whileHover={{ y: -4, scale: 1.02 }}
                  className="glass rounded-xl p-4 group cursor-default"
                >
                  <div className="text-xl mb-2">{emoji}</div>
                  <h3 className="text-[13px] font-semibold text-white/80 mb-1 group-hover:text-white transition-colors">
                    {title}
                  </h3>
                  <p className="text-[11px] text-white/30 leading-relaxed">
                    {description}
                  </p>
                </motion.div>
              ))}
            </motion.div>
          </div>
        </motion.div>

        {/* ================================
            RIGHT PANEL — Login Form
            ================================ */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.5, delay: 0.1 }}
          className="w-full lg:w-[45%] xl:w-[42%] flex items-center justify-center p-6 sm:p-8 relative"
        >
          {/* Subtle background for right panel */}
          <div className="absolute inset-0 bg-gradient-to-br from-navy-950 via-navy-900/50 to-navy-950" />

          {/* Mobile-only logo */}
          <div className="absolute top-6 left-6 flex items-center gap-2 lg:hidden">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-brand-purple to-brand-indigo flex items-center justify-center">
              <Dna className="w-4 h-4 text-white" strokeWidth={2.5} />
            </div>
            <span className="text-sm font-bold tracking-tight text-white">
              Decision<span className="gradient-text-brand">DNA</span>
            </span>
          </div>

          <div className="relative z-10 w-full max-w-[440px]">
            <LoginCard
              form={form}
              errors={errors}
              isLoading={state === "validating"}
              onUpdateField={updateField}
              onSubmit={handleSubmit}
            />

            {/* Footer */}
            <motion.p
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 1 }}
              className="text-center text-[11px] text-white/15 mt-6"
            >
              © 2026 DecisionDNA AI. All rights reserved.
            </motion.p>
          </div>
        </motion.div>
      </div>
    </>
  );
}
