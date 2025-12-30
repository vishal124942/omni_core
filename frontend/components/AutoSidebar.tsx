"use client";

import { motion, AnimatePresence } from "framer-motion";
import {
    BarChart3,
    Linkedin,
    Twitter,
    FileText,
    Mail,
    Zap,
    Image as ImageIcon,
    Search,
    CheckCircle2,
    Loader2,
    Circle
} from "lucide-react";
import { cn } from "@/lib/utils";

interface SidebarItemProps {
    id: string;
    label: string;
    icon: any;
    status: "pending" | "active" | "completed";
    progress?: number;
    isActive: boolean;
    onClick: (id: string) => void;
}

function SidebarItem({ id, label, icon: Icon, status, progress, isActive, onClick }: SidebarItemProps) {
    return (
        <button
            onClick={() => onClick(id)}
            className={cn(
                "group relative flex items-center gap-3 w-full p-3 rounded-xl transition-all duration-300",
                isActive
                    ? "bg-white/10 border border-white/20 shadow-[0_0_20px_rgba(255,255,255,0.05)]"
                    : "hover:bg-white/5 border border-transparent"
            )}
        >
            <div className={cn(
                "p-2 rounded-lg transition-colors duration-300",
                status === "completed" ? "text-cyber-green" :
                    status === "active" ? "text-cyber-cyan" : "text-white/20"
            )}>
                <Icon className="w-5 h-5" />
            </div>

            <div className="flex flex-col items-start flex-1 min-w-0">
                <span className={cn(
                    "text-xs font-bold uppercase tracking-widest transition-colors duration-300 truncate w-full text-left",
                    status === "completed" ? "text-white" :
                        status === "active" ? "text-cyber-cyan" : "text-white/40"
                )}>
                    {label}
                </span>
                <div className="flex items-center gap-2 w-full">
                    <span className="text-[10px] font-mono text-white/20 uppercase whitespace-nowrap">
                        {status === "completed" ? "Ready" : status === "active" ? `${progress || 0}%` : "Waiting"}
                    </span>
                    {status === "active" && (
                        <div className="h-[2px] flex-1 bg-white/5 rounded-full overflow-hidden">
                            <motion.div
                                initial={{ width: 0 }}
                                animate={{ width: `${progress || 0}%` }}
                                className="h-full bg-cyber-cyan"
                            />
                        </div>
                    )}
                </div>
            </div>

            <div className="ml-auto shrink-0">
                {status === "completed" && (
                    <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }}>
                        <CheckCircle2 className="w-4 h-4 text-cyber-green" />
                    </motion.div>
                )}
                {status === "active" && (
                    <Loader2 className="w-4 h-4 text-cyber-cyan animate-spin" />
                )}
                {status === "pending" && (
                    <Circle className="w-4 h-4 text-white/10" />
                )}
            </div>

            {isActive && (
                <motion.div
                    layoutId="sidebar-active-indicator"
                    className="absolute left-0 w-1 h-6 bg-cyber-cyan rounded-r-full"
                />
            )}
        </button>
    );
}

interface AutoSidebarProps {
    steps: {
        id: string;
        label: string;
        icon: any;
        status: "pending" | "active" | "completed";
        progress?: number;
    }[];
    activeSection: string;
    onSectionClick: (id: string) => void;
    isBotActive: boolean;
}

export function AutoSidebar({ steps, activeSection, onSectionClick, isBotActive }: AutoSidebarProps) {
    return (
        <div className="w-72 h-full bg-cyber-black/40 border-r border-white/10 backdrop-blur-xl flex flex-col p-6">
            {/* Bot Section */}
            <div className="flex flex-col items-center mb-12 mt-4">
                <div className="relative">
                    {/* The Glowing Orb */}
                    <motion.div
                        animate={{
                            scale: isBotActive ? [1, 1.2, 1] : 1,
                            opacity: isBotActive ? [0.5, 0.8, 0.5] : 0.3,
                            boxShadow: isBotActive
                                ? [
                                    "0 0 20px rgba(0, 245, 255, 0.2)",
                                    "0 0 40px rgba(0, 245, 255, 0.5)",
                                    "0 0 20px rgba(0, 245, 255, 0.2)"
                                ]
                                : "0 0 10px rgba(255, 255, 255, 0.1)"
                        }}
                        transition={{
                            duration: 2,
                            repeat: Infinity,
                            ease: "easeInOut"
                        }}
                        className={cn(
                            "w-20 h-20 rounded-full border-2 transition-colors duration-500",
                            isBotActive ? "border-cyber-cyan bg-cyber-cyan/20" : "border-white/10 bg-white/5"
                        )}
                    />

                    {/* Inner Core */}
                    <motion.div
                        animate={isBotActive ? {
                            scale: [0.8, 1, 0.8],
                            opacity: [0.4, 0.7, 0.4]
                        } : {}}
                        transition={{ duration: 1.5, repeat: Infinity }}
                        className={cn(
                            "absolute inset-5 rounded-full blur-sm",
                            isBotActive ? "bg-cyber-cyan" : "bg-white/10"
                        )}
                    />
                </div>

                <div className="mt-6 text-center">
                    <h3 className="text-[10px] font-mono uppercase tracking-[0.3em] text-white/40">
                        Autonomous Agent
                    </h3>
                    <p className="text-sm font-bold text-white mt-1">
                        {isBotActive ? "Analyzing Data..." : "System Idle"}
                    </p>
                </div>
            </div>

            {/* Navigation Items */}
            <div className="flex-1 space-y-2 overflow-y-auto custom-scrollbar pr-2">
                <div className="text-[10px] font-mono uppercase tracking-widest text-white/20 mb-4 ml-2">
                    Content Pipeline
                </div>
                {steps.map((step) => (
                    <SidebarItem
                        key={step.id}
                        id={step.id}
                        label={step.label}
                        icon={step.icon}
                        status={step.status as any}
                        progress={step.progress}
                        isActive={activeSection === step.id}
                        onClick={onSectionClick}
                    />
                ))}
            </div>

            {/* Bottom Status */}
            <div className="mt-auto pt-6 border-t border-white/5">
                <div className="flex items-center justify-between text-[10px] font-mono uppercase tracking-widest text-white/20">
                    <span>Neural Link</span>
                    <span className={cn(isBotActive ? "text-cyber-green" : "text-white/10")}>
                        {isBotActive ? "Online" : "Standby"}
                    </span>
                </div>
                <div className="mt-2 h-1 w-full bg-white/5 rounded-full overflow-hidden">
                    <motion.div
                        animate={isBotActive ? {
                            x: ["-100%", "100%"]
                        } : { x: "-100%" }}
                        transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
                        className="h-full w-1/3 bg-cyber-cyan/50"
                    />
                </div>
                <div className="mt-4 text-[8px] font-mono text-white/10 uppercase tracking-tighter text-center">
                    v4.2.0 // Secure Protocol // AES-256
                </div>
            </div>
        </div>
    );
}
