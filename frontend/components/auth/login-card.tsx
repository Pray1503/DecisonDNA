"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Eye, EyeOff, ArrowRight, Dna, Building2, Lock, Mail } from "lucide-react";
import { SSOButtons } from "./sso-buttons";
import { SecurityBadge } from "./security-badge";
import { ForgotPasswordModal } from "./forgot-password-modal";
import type { LoginForm } from "@/hooks/use-login";

interface LoginCardProps {
  form: LoginForm;
  errors: Partial<Record<keyof LoginForm, string>>;
  isLoading: boolean;
  onUpdateField: (field: keyof LoginForm, value: string | boolean) => void;
  onSubmit: () => void;
}

export function LoginCard({
  form,
  errors,
  isLoading,
  onUpdateField,
  onSubmit,
}: LoginCardProps) {
  const [showPassword, setShowPassword] = useState(false);
  const [showForgotModal, setShowForgotModal] = useState(false);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      onSubmit();
    }
  };

  return (
    <>
      <motion.div
        initial={{ opacity: 0, y: 30, scale: 0.97 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={{ duration: 0.7, ease: [0.16, 1, 0.3, 1] }}
        className="glass-card rounded-3xl p-8 sm:p-10 w-full max-w-[440px] mx-auto"
      >
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.15, duration: 0.5 }}
          className="text-center mb-8"
        >
          {/* Logo */}
          <div className="flex items-center justify-center gap-2.5 mb-5">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-brand-purple to-brand-indigo flex items-center justify-center shadow-lg shadow-brand-purple/20">
              <Dna className="w-5 h-5 text-white" strokeWidth={2.5} />
            </div>
            <span className="text-lg font-bold tracking-tight text-white">
              Decision<span className="gradient-text-brand">DNA</span> AI
            </span>
          </div>

          <h1 className="text-[22px] font-bold text-white tracking-tight">
            Welcome Back
          </h1>
          <p className="text-[13px] text-white/40 mt-1.5">
            Sign in to your organization&apos;s workspace
          </p>
        </motion.div>

        {/* Form */}
        <div className="space-y-4" onKeyDown={handleKeyDown}>
          {/* Email */}
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2, duration: 0.4 }}
          >
            <label
              htmlFor="email"
              className="block text-[11px] font-semibold uppercase tracking-wider text-white/40 mb-1.5"
            >
              Work Email
            </label>
            <div className="relative">
              <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-white/20" />
              <input
                id="email"
                type="email"
                value={form.email}
                onChange={(e) => onUpdateField("email", e.target.value)}
                placeholder="john.doe@company.com"
                className={`glass-input w-full rounded-xl pl-10 pr-4 py-3 text-sm text-white placeholder:text-white/20 outline-none
                  ${errors.email ? "border-red-500/50 bg-red-500/[0.03]" : ""}`}
                autoComplete="email"
                aria-label="Work email address"
                aria-invalid={!!errors.email}
              />
            </div>
            {errors.email && (
              <motion.p
                initial={{ opacity: 0, y: -4 }}
                animate={{ opacity: 1, y: 0 }}
                className="text-[11px] text-red-400 mt-1 ml-1"
              >
                {errors.email}
              </motion.p>
            )}
          </motion.div>

          {/* Password */}
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.28, duration: 0.4 }}
          >
            <label
              htmlFor="password"
              className="block text-[11px] font-semibold uppercase tracking-wider text-white/40 mb-1.5"
            >
              Password
            </label>
            <div className="relative">
              <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-white/20" />
              <input
                id="password"
                type={showPassword ? "text" : "password"}
                value={form.password}
                onChange={(e) => onUpdateField("password", e.target.value)}
                placeholder="••••••••"
                className={`glass-input w-full rounded-xl pl-10 pr-12 py-3 text-sm text-white placeholder:text-white/20 outline-none
                  ${errors.password ? "border-red-500/50 bg-red-500/[0.03]" : ""}`}
                autoComplete="current-password"
                aria-label="Password"
                aria-invalid={!!errors.password}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 p-1 text-white/20 hover:text-white/50 transition-colors cursor-pointer"
                aria-label={showPassword ? "Hide password" : "Show password"}
              >
                {showPassword ? (
                  <EyeOff className="w-4 h-4" />
                ) : (
                  <Eye className="w-4 h-4" />
                )}
              </button>
            </div>
            {errors.password && (
              <motion.p
                initial={{ opacity: 0, y: -4 }}
                animate={{ opacity: 1, y: 0 }}
                className="text-[11px] text-red-400 mt-1 ml-1"
              >
                {errors.password}
              </motion.p>
            )}
          </motion.div>

          {/* Organization Code */}
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.36, duration: 0.4 }}
          >
            <label
              htmlFor="orgCode"
              className="block text-[11px] font-semibold uppercase tracking-wider text-white/40 mb-1.5"
            >
              Organization Code
            </label>
            <div className="relative">
              <Building2 className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-white/20" />
              <input
                id="orgCode"
                type="text"
                value={form.orgCode}
                onChange={(e) => onUpdateField("orgCode", e.target.value)}
                placeholder="ORG-ACME-001"
                className={`glass-input w-full rounded-xl pl-10 pr-4 py-3 text-sm text-white placeholder:text-white/20 outline-none font-mono
                  ${errors.orgCode ? "border-red-500/50 bg-red-500/[0.03]" : ""}`}
                aria-label="Organization code"
                aria-invalid={!!errors.orgCode}
              />
            </div>
            {errors.orgCode && (
              <motion.p
                initial={{ opacity: 0, y: -4 }}
                animate={{ opacity: 1, y: 0 }}
                className="text-[11px] text-red-400 mt-1 ml-1"
              >
                {errors.orgCode}
              </motion.p>
            )}
          </motion.div>

          {/* Remember me + Forgot password */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.44, duration: 0.4 }}
            className="flex items-center justify-between pt-1"
          >
            <label className="flex items-center gap-2 cursor-pointer group">
              <input
                type="checkbox"
                checked={form.rememberMe}
                onChange={(e) => onUpdateField("rememberMe", e.target.checked)}
                className="w-3.5 h-3.5 rounded border border-white/10 bg-white/[0.03] accent-brand-purple cursor-pointer"
                aria-label="Remember me"
              />
              <span className="text-[12px] text-white/30 group-hover:text-white/50 transition-colors">
                Remember me
              </span>
            </label>
            <button
              type="button"
              onClick={() => setShowForgotModal(true)}
              className="text-[12px] text-brand-purple/70 hover:text-brand-purple transition-colors cursor-pointer"
            >
              Forgot password?
            </button>
          </motion.div>

          {/* Submit */}
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5, duration: 0.4 }}
            className="pt-2"
          >
            <motion.button
              onClick={onSubmit}
              disabled={isLoading}
              whileHover={{ scale: 1.01 }}
              whileTap={{ scale: 0.99 }}
              className="btn-glow w-full py-3.5 rounded-xl bg-gradient-to-r from-brand-purple via-brand-indigo to-brand-blue
                         text-white text-sm font-semibold flex items-center justify-center gap-2
                         disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer
                         shadow-lg shadow-brand-purple/15
                         hover:shadow-xl hover:shadow-brand-purple/25
                         transition-all duration-300"
              aria-label="Sign in"
            >
              {isLoading ? (
                <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              ) : (
                <>
                  <span>Sign In</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </motion.button>
          </motion.div>
        </div>

        {/* SSO */}
        <SSOButtons />

        {/* Security */}
        <SecurityBadge />
      </motion.div>

      {/* Forgot Password Modal */}
      <ForgotPasswordModal
        isOpen={showForgotModal}
        onClose={() => setShowForgotModal(false)}
      />
    </>
  );
}
