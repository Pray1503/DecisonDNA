"use client";

import { useEffect, useRef } from "react";
import { motion } from "framer-motion";
import {
  Brain,
  GitBranch,
  FileText,
  Users,
  Network,
  Zap,
  Database,
  Shield,
  BarChart3,
  MessageSquare,
} from "lucide-react";

const FLOATING_ICONS = [
  { Icon: Brain, x: "15%", y: "20%", delay: 0, size: 28, color: "#a78bfa" },
  { Icon: GitBranch, x: "75%", y: "15%", delay: 0.5, size: 24, color: "#60a5fa" },
  { Icon: FileText, x: "25%", y: "70%", delay: 1, size: 22, color: "#34d399" },
  { Icon: Users, x: "80%", y: "65%", delay: 1.5, size: 26, color: "#f472b6" },
  { Icon: Network, x: "50%", y: "35%", delay: 2, size: 30, color: "#818cf8" },
  { Icon: Zap, x: "60%", y: "80%", delay: 0.8, size: 20, color: "#fbbf24" },
  { Icon: Database, x: "35%", y: "50%", delay: 1.2, size: 22, color: "#06b6d4" },
  { Icon: Shield, x: "85%", y: "40%", delay: 1.8, size: 20, color: "#a78bfa" },
  { Icon: BarChart3, x: "10%", y: "45%", delay: 0.3, size: 24, color: "#10b981" },
  { Icon: MessageSquare, x: "70%", y: "50%", delay: 2.2, size: 18, color: "#f97316" },
];

function Particles() {
  return (
    <div className="absolute inset-0 overflow-hidden pointer-events-none">
      {Array.from({ length: 30 }).map((_, i) => (
        <div
          key={i}
          className="absolute rounded-full"
          style={{
            width: `${Math.random() * 3 + 1}px`,
            height: `${Math.random() * 3 + 1}px`,
            left: `${Math.random() * 100}%`,
            top: `${Math.random() * 100}%`,
            background: `rgba(${139 + Math.random() * 60}, ${92 + Math.random() * 80}, ${246}, ${0.2 + Math.random() * 0.3})`,
            animation: `particle-drift ${10 + Math.random() * 10}s linear ${Math.random() * 8}s infinite`,
          }}
        />
      ))}
    </div>
  );
}

export function BackgroundAnimation() {
  return (
    <div className="absolute inset-0 overflow-hidden">
      {/* Gradient mesh background */}
      <div className="absolute inset-0 bg-gradient-to-br from-navy-950 via-navy-900 to-navy-800" />

      {/* Radial glow blobs */}
      <div
        className="absolute w-[600px] h-[600px] rounded-full opacity-20"
        style={{
          background: "radial-gradient(circle, rgba(139, 92, 246, 0.4) 0%, transparent 70%)",
          left: "10%",
          top: "20%",
          animation: "glow-pulse 6s ease-in-out infinite",
        }}
      />
      <div
        className="absolute w-[500px] h-[500px] rounded-full opacity-15"
        style={{
          background: "radial-gradient(circle, rgba(99, 102, 241, 0.35) 0%, transparent 70%)",
          right: "5%",
          bottom: "10%",
          animation: "glow-pulse 8s ease-in-out 2s infinite",
        }}
      />
      <div
        className="absolute w-[400px] h-[400px] rounded-full opacity-10"
        style={{
          background: "radial-gradient(circle, rgba(59, 130, 246, 0.3) 0%, transparent 70%)",
          left: "50%",
          top: "60%",
          animation: "glow-pulse 7s ease-in-out 1s infinite",
        }}
      />

      {/* Grid pattern overlay */}
      <div
        className="absolute inset-0 opacity-[0.03]"
        style={{
          backgroundImage:
            "linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px)",
          backgroundSize: "60px 60px",
        }}
      />

      {/* Floating icons */}
      {FLOATING_ICONS.map(({ Icon, x, y, delay, size, color }, i) => (
        <motion.div
          key={i}
          className="absolute"
          style={{ left: x, top: y }}
          initial={{ opacity: 0, scale: 0 }}
          animate={{ opacity: 0.15, scale: 1 }}
          transition={{ delay: delay + 0.5, duration: 0.8, ease: "easeOut" }}
        >
          <motion.div
            animate={{
              y: [-8, 8, -8],
              rotate: [-3, 3, -3],
            }}
            transition={{
              duration: 5 + delay,
              repeat: Infinity,
              ease: "easeInOut",
            }}
          >
            <Icon size={size} color={color} strokeWidth={1.5} />
          </motion.div>
        </motion.div>
      ))}

      {/* Particles */}
      <Particles />
    </div>
  );
}
