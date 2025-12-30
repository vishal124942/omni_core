"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Check, Loader2, AlertCircle, FileText, Brain, Share2, Scissors, Database } from "lucide-react";
import { cn } from "@/lib/utils";
import { GlassCard } from "./GlassCard";

export type StepStatus = "pending" | "active" | "completed" | "error" | "skipped";

export interface PipelineStep {
    id: string;
    label: string;
    description: string;
    icon: any;
    status: StepStatus;
    progress?: number;
}

interface PipelineTrackerProps {
    steps: PipelineStep[];
}

export function PipelineTracker({ steps }: PipelineTrackerProps) {
    const [hasMounted, setHasMounted] = useState(false);

    useEffect(() => {
        setHasMounted(true);
    }, []);

    if (!hasMounted) return <div className="grid grid-cols-1 md:grid-cols-5 gap-4 h-32" />;

    return (
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
            {steps.map((step, index) => {
                const Icon = step.icon;
                const isActive = step.status === "active";
                const isCompleted = step.status === "completed";
                const isError = step.status === "error";
                const isSkipped = step.status === "skipped";

                return (
                    <div key={step.id} className="relative">
                        <GlassCard
                            className={cn(
                                "h-full transition-all duration-500",
                                isActive && "border-cyber-cyan shadow-[0_0_20px_rgba(0,245,255,0.1)]",
                                isError && "border-cyber-red shadow-[0_0_20px_rgba(255,0,60,0.1)]",
                                isSkipped && "opacity-30 border-white/5 grayscale"
                            )}
                        >
                            <div className="flex flex-col items-center text-center space-y-3">
                                <motion.div
                                    animate={isActive ? {
                                        scale: [1, 1.1, 1],
                                        borderColor: ["#00f5ff", "#00f5ff33", "#00f5ff"]
                                    } : {}}
                                    transition={{ duration: 2, repeat: Infinity }}
                                    className={cn(
                                        "w-12 h-12 rounded-xl border flex items-center justify-center transition-colors duration-500",
                                        isCompleted ? "bg-cyber-green/20 border-cyber-green text-cyber-green" :
                                            isActive ? "bg-cyber-cyan/20 border-cyber-cyan text-cyber-cyan" :
                                                isError ? "bg-cyber-red/20 border-cyber-red text-cyber-red" :
                                                    isSkipped ? "bg-black/20 border-white/5 text-white/10" :
                                                        "bg-white/5 border-white/10 text-white/20"
                                    )}
                                >
                                    <Icon className="w-6 h-6" />
                                </motion.div>

                                <div>
                                    <h3 className={cn(
                                        "text-xs font-bold uppercase tracking-widest transition-colors duration-500",
                                        (isActive || isCompleted) ? "text-white" :
                                            isSkipped ? "text-white/10" : "text-white/20"
                                    )}>
                                        {step.label}
                                    </h3>
                                    <p className={cn("text-[10px] font-mono mt-1", isSkipped ? "text-white/10" : "text-white/40")}>
                                        {isSkipped ? "SKIPPED" : step.description}
                                    </p>
                                </div>

                                {/* Progress Bar */}
                                {(isActive || isCompleted) && (
                                    <div className="w-full space-y-1">
                                        <div className="flex justify-between text-[8px] font-mono text-white/40 uppercase tracking-tighter">
                                            <span>Progress</span>
                                            <span>{step.progress || (isCompleted ? 100 : 0)}%</span>
                                        </div>
                                        <div className="h-1 w-full bg-white/5 rounded-full overflow-hidden">
                                            <motion.div
                                                initial={{ width: 0 }}
                                                animate={{ width: `${step.progress || (isCompleted ? 100 : 0)}%` }}
                                                className={cn(
                                                    "h-full transition-all duration-500",
                                                    isCompleted ? "bg-cyber-green" : "bg-cyber-cyan"
                                                )}
                                            />
                                        </div>
                                    </div>
                                )}
                            </div>
                        </GlassCard>

                        {index < steps.length - 1 && (
                            <div className={cn("hidden md:block absolute top-1/2 -right-2 w-4 h-[1px]", isSkipped ? "bg-white/5" : "bg-white/10")} />
                        )}
                    </div>
                );
            })}
        </div>
    );
}
