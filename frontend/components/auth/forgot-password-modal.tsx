"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Mail, ArrowRight, CheckCircle2 } from "lucide-react";

interface ForgotPasswordModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function ForgotPasswordModal({ isOpen, onClose }: ForgotPasswordModalProps) {
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) return;
    setLoading(true);
    await new Promise((r) => setTimeout(r, 1200));
    setLoading(false);
    setSent(true);
  };

  const handleClose = () => {
    onClose();
    // Reset after animation
    setTimeout(() => {
      setEmail("");
      setSent(false);
    }, 300);
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm"
            onClick={handleClose}
          />

          {/* Modal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            transition={{ type: "spring", damping: 25, stiffness: 300 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4"
          >
            <div
              className="glass-card rounded-2xl p-8 w-full max-w-md relative"
              onClick={(e) => e.stopPropagation()}
            >
              {/* Close button */}
              <button
                onClick={handleClose}
                className="absolute top-4 right-4 p-1.5 rounded-lg text-white/30 hover:text-white/60 hover:bg-white/[0.05] transition-all cursor-pointer"
                aria-label="Close modal"
              >
                <X className="w-4 h-4" />
              </button>

              <AnimatePresence mode="wait">
                {!sent ? (
                  <motion.div
                    key="form"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0, x: -20 }}
                  >
                    <div className="flex items-center gap-3 mb-6">
                      <div className="w-10 h-10 rounded-xl bg-brand-purple/10 border border-brand-purple/20 flex items-center justify-center">
                        <Mail className="w-5 h-5 text-brand-purple" />
                      </div>
                      <div>
                        <h3 className="text-lg font-semibold text-white">Reset Password</h3>
                        <p className="text-xs text-white/40">We&apos;ll send a reset link to your work email</p>
                      </div>
                    </div>

                    <form onSubmit={handleSubmit}>
                      <label className="block text-[11px] font-semibold uppercase tracking-wider text-white/40 mb-2">
                        Work Email Address
                      </label>
                      <input
                        type="email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        placeholder="john.doe@company.com"
                        className="glass-input w-full rounded-xl px-4 py-3 text-sm text-white placeholder:text-white/20 outline-none mb-4"
                        autoFocus
                        required
                      />

                      <motion.button
                        type="submit"
                        disabled={loading || !email}
                        whileHover={{ scale: 1.01 }}
                        whileTap={{ scale: 0.99 }}
                        className="w-full py-3 rounded-xl bg-gradient-to-r from-brand-purple to-brand-indigo
                                   text-white text-sm font-semibold flex items-center justify-center gap-2
                                   disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer
                                   hover:shadow-lg hover:shadow-brand-purple/20 transition-shadow"
                      >
                        {loading ? (
                          <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                        ) : (
                          <>
                            <span>Send Reset Link</span>
                            <ArrowRight className="w-4 h-4" />
                          </>
                        )}
                      </motion.button>
                    </form>
                  </motion.div>
                ) : (
                  <motion.div
                    key="success"
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    className="text-center py-4"
                  >
                    <motion.div
                      initial={{ scale: 0 }}
                      animate={{ scale: 1 }}
                      transition={{ type: "spring", damping: 12, stiffness: 200 }}
                      className="w-16 h-16 rounded-full bg-brand-emerald/10 border border-brand-emerald/20 flex items-center justify-center mx-auto mb-4"
                    >
                      <CheckCircle2 className="w-8 h-8 text-brand-emerald" />
                    </motion.div>
                    <h3 className="text-lg font-semibold text-white mb-2">Check Your Inbox</h3>
                    <p className="text-sm text-white/40 mb-6">
                      We&apos;ve sent a password reset link to <strong className="text-white/60">{email}</strong>
                    </p>
                    <button
                      onClick={handleClose}
                      className="text-sm text-brand-purple hover:text-brand-violet transition-colors cursor-pointer"
                    >
                      Back to Login
                    </button>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
