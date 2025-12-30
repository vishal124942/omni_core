"use client";

import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Brain, Sparkles } from "lucide-react";
import { cn } from "@/lib/utils";

interface ThinkingIndicatorProps {
  isVisible: boolean;
  currentStep: string;
  stepLabel: string;
  streamingText: string;
}

export function ThinkingIndicator({ isVisible, currentStep, stepLabel, streamingText }: ThinkingIndicatorProps) {
  const [dots, setDots] = useState("");
  const [hasMounted, setHasMounted] = useState(false);
  const textRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setHasMounted(true);
  }, []);

  // Animate the thinking dots
  useEffect(() => {
    if (!isVisible) return;

    const interval = setInterval(() => {
      setDots(prev => prev.length >= 3 ? "" : prev + ".");
    }, 400);

    return () => clearInterval(interval);
  }, [isVisible]);

  // Auto-scroll to bottom as new text appears
  useEffect(() => {
    if (textRef.current) {
      textRef.current.scrollTop = textRef.current.scrollHeight;
    }
  }, [streamingText]);

  if (!hasMounted) return null;

  return (
    <AnimatePresence>
      {isVisible && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: "auto" }}
          exit={{ opacity: 0, height: 0 }}
          className="w-full border-b border-cyber-cyan/20 bg-black/60 backdrop-blur-md overflow-hidden"
        >
          <div className="w-full h-[1px] bg-gradient-to-r from-transparent via-cyber-cyan to-transparent opacity-50" />

          <div className="max-w-[1400px] mx-auto px-6 py-2 flex items-center justify-between gap-6">
            {/* Left: Status & Icon */}
            <div className="flex items-center gap-3 shrink-0">
              <div className="relative">
                <motion.div
                  animate={{ rotate: 360 }}
                  transition={{ duration: 3, repeat: Infinity, ease: "linear" }}
                  className="w-4 h-4 text-cyber-cyan"
                >
                  <Brain className="w-full h-full" />
                </motion.div>
                <div className="absolute inset-0 bg-cyber-cyan/20 blur-md rounded-full animate-pulse" />
              </div>

              <div className="flex flex-col">
                <div className="flex items-center gap-2">
                  <span className="text-[10px] font-mono text-cyber-cyan font-bold uppercase tracking-widest leading-none">
                    NEURAL LINK BUSY
                  </span>
                  <span className="text-[10px] font-mono text-white/40 leading-none">{dots}</span>
                </div>
                <span className="text-xs text-white font-medium truncate leading-normal">
                  {stepLabel}
                </span>
              </div>
            </div>

            {/* Right: Streaming Text (Single Line) */}
            <div className="flex-1 min-w-0 flex justify-end">
              <div className="relative max-w-2xl px-4 py-1.5 rounded-full bg-white/5 border border-white/10 flex items-center gap-2">
                <Sparkles className="w-3 h-3 text-cyber-purple shrink-0" />
                <span className="text-[10px] font-mono text-white/70 truncate">
                  {streamingText || "Processing..."}
                </span>
                <motion.span
                  animate={{ opacity: [1, 0] }}
                  transition={{ duration: 0.5, repeat: Infinity }}
                  className="w-1.5 h-1.5 bg-cyber-purple rounded-full shrink-0"
                />
              </div>
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
