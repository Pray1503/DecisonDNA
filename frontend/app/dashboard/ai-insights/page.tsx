"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Sparkles, Send, Brain, Bot, User, AlertTriangle } from "lucide-react";
import { api } from "@/lib/api";

interface Message {
  role: "user" | "assistant";
  content: string;
}

const SUGGESTIONS = [
  "Why did we migrate to event-driven architecture?",
  "What cache layer did we implement for backstage?",
  "Show incidents related to database connections",
  "Summarize key decisions made for security updates",
];

export default function AIInsightsPage() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content:
        "Hello! I am your DecisionDNA AI Assistant. I can traverse your 33k+ engineering artifacts and 500 decisions to answer questions about architecture choices, system designs, history, and technical choices. What would you like to know?",
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSend = async (textToSend?: string) => {
    const queryText = textToSend || input;
    if (!queryText.trim() || loading) return;

    setInput("");
    const newMessages = [...messages, { role: "user" as const, content: queryText }];
    setMessages(newMessages);
    setLoading(true);

    try {
      const res = await api.query(queryText);
      setMessages([...newMessages, { role: "assistant" as const, content: res.response }]);
    } catch (e) {
      setMessages([
        ...newMessages,
        {
          role: "assistant" as const,
          content:
            "⚠️ Error: I couldn't communicate with the backend. Please check if your FastAPI backend is running on port 8000.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 h-[calc(100vh-8rem)] flex flex-col">
      {/* Header */}
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="flex-shrink-0">
        <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-3">
          <Sparkles className="w-7 h-7 text-brand-purple" />
          AI Insights Portal
        </h1>
        <p className="text-sm text-white/30 mt-1">
          Grounded chat assistant running on your decision graph & database
        </p>
      </motion.div>

      {/* Main chat layout */}
      <div className="flex-1 min-h-0 grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Chat area */}
        <div className="lg:col-span-3 glass-card rounded-2xl flex flex-col overflow-hidden h-full">
          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-6 space-y-4">
            {messages.map((msg, i) => (
              <div
                key={i}
                className={`flex gap-3 max-w-[85%] ${
                  msg.role === "user" ? "ml-auto flex-row-reverse" : "mr-auto"
                }`}
              >
                <div
                  className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${
                    msg.role === "user"
                      ? "bg-brand-purple/20 text-brand-purple border border-brand-purple/30"
                      : "bg-brand-blue/20 text-brand-blue border border-brand-blue/30"
                  }`}
                >
                  {msg.role === "user" ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
                </div>
                <div
                  className={`rounded-2xl p-4 text-sm leading-relaxed border ${
                    msg.role === "user"
                      ? "bg-brand-purple/10 border-brand-purple/15 text-white"
                      : "bg-white/[0.02] border-white/[0.04] text-white/80"
                  }`}
                >
                  {/* Clean linebreaks for markdown responses */}
                  <div className="whitespace-pre-line prose prose-invert max-w-none text-xs leading-normal">
                    {msg.content}
                  </div>
                </div>
              </div>
            ))}
            {loading && (
              <div className="flex gap-3 mr-auto max-w-[80%]">
                <div className="w-8 h-8 rounded-lg bg-brand-blue/20 text-brand-blue border border-brand-blue/30 flex items-center justify-center animate-pulse">
                  <Bot className="w-4 h-4" />
                </div>
                <div className="bg-white/[0.02] border border-white/[0.04] rounded-2xl p-4 text-xs text-white/40 flex items-center gap-2">
                  <div className="w-3 h-3 border-2 border-white/20 border-t-white rounded-full animate-spin" />
                  <span>Traversing decisions and graph memory...</span>
                </div>
              </div>
            )}
          </div>

          {/* Form */}
          <div className="p-4 border-t border-white/[0.04] bg-navy-950/40">
            <div className="flex gap-2">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSend()}
                placeholder="Ask about architectural choices... (e.g. 'Why did we choose Redis?')"
                className="flex-1 glass-input rounded-xl px-4 py-3 text-sm text-white placeholder:text-white/20 outline-none"
              />
              <button
                onClick={() => handleSend()}
                disabled={loading || !input.trim()}
                className="w-12 h-12 rounded-xl bg-gradient-to-r from-brand-purple to-brand-indigo flex items-center justify-center text-white disabled:opacity-30 disabled:cursor-not-allowed hover:shadow-lg hover:shadow-brand-purple/15 transition-all cursor-pointer flex-shrink-0"
              >
                <Send className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>

        {/* Suggestion panel */}
        <div className="glass-card rounded-2xl p-6 flex flex-col space-y-4 h-full overflow-y-auto">
          <div>
            <h3 className="text-sm font-semibold text-white">Suggested Queries</h3>
            <p className="text-[11px] text-white/25 mt-0.5">Click to ask the AI assistant</p>
          </div>
          <div className="space-y-2">
            {SUGGESTIONS.map((s) => (
              <button
                key={s}
                onClick={() => handleSend(s)}
                disabled={loading}
                className="w-full text-left p-3 rounded-xl bg-white/[0.02] border border-white/[0.04] hover:bg-white/[0.05] hover:border-white/[0.08] transition-all text-xs text-white/60 hover:text-white leading-relaxed cursor-pointer"
              >
                {s}
              </button>
            ))}
          </div>
          <div className="pt-4 border-t border-white/[0.04] flex items-start gap-2.5">
            <Brain className="w-4 h-4 text-brand-purple flex-shrink-0 mt-0.5" />
            <p className="text-[10px] text-white/20 leading-normal">
              Queries are evaluated using direct SQLite search for structured decisions, falling back to network path searches over the Evidence Graph.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
