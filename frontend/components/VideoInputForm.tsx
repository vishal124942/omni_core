"use client";

import { useState } from "react";
import { GlassCard } from "./GlassCard";
import { NeonButton } from "./NeonButton";
import { motion, AnimatePresence } from "framer-motion";
import { Link as LinkIcon, User, Zap, AlertTriangle } from "lucide-react";

import { cn } from "@/lib/utils";

interface VideoInputFormProps {
    onSubmit: (data: {
        videoUrl: string;
        clientId: string;
        toneProfile: string;
        platforms: string[];
    }) => void;
    isLoading: boolean;
    variant?: "default" | "minimal";
}

const PLATFORMS = [
    { id: "twitter", label: "Twitter / X", color: "text-white" },
    { id: "linkedin", label: "LinkedIn", color: "text-cyber-blue" },
    { id: "blog", label: "SEO Blog", color: "text-cyber-magenta" },
    { id: "newsletter", label: "Newsletter", color: "text-cyber-yellow" },
    { id: "audio", label: "Neural Audio", color: "text-cyber-cyan" },
    { id: "visuals", label: "Visual Studio", color: "text-cyber-green" }
];

export function VideoInputForm({ onSubmit, isLoading, variant = "default" }: VideoInputFormProps) {
    const [videoUrl, setVideoUrl] = useState("");
    const [clientId, setClientId] = useState("default_client");
    const [toneProfile, setToneProfile] = useState("professional");
    const [selectedPlatforms, setSelectedPlatforms] = useState<string[]>(PLATFORMS.map(p => p.id));
    const [error, setError] = useState<string | null>(null);

    const togglePlatform = (id: string) => {
        setSelectedPlatforms(prev =>
            prev.includes(id) ? prev.filter(p => p !== id) : [...prev, id]
        );
    };

    const validateUrl = (url: string) => {
        const youtubeRegex = /^(https?:\/\/)?(www\.)?(youtube\.com|youtu\.be)\/.+/;
        const vimeoRegex = /^(https?:\/\/)?(www\.)?(vimeo\.com)\/.+/;
        const generalVideoRegex = /^(https?:\/\/).+(\.(mp4|mov|avi|wmv|flv|mkv))$/i;

        if (!url.trim()) return "URL is required";
        if (!youtubeRegex.test(url) && !vimeoRegex.test(url) && !generalVideoRegex.test(url)) {
            return "Please enter a valid YouTube, Vimeo, or direct video URL";
        }
        return null;
    };

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        setError(null);

        const validationError = validateUrl(videoUrl);
        if (validationError) {
            setError(validationError);
            return;
        }

        onSubmit({ videoUrl, clientId, toneProfile, platforms: selectedPlatforms });
    };

    if (variant === "minimal") {
        return (
            <form onSubmit={handleSubmit} className="flex gap-2 w-full">
                <div className="relative flex-1">
                    <LinkIcon className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-cyber-cyan/50" />
                    <input
                        type="text"
                        value={videoUrl}
                        onChange={(e) => {
                            setVideoUrl(e.target.value);
                            if (error) setError(null);
                        }}
                        placeholder="Paste YouTube URL..."
                        className={cn(
                            "w-full bg-cyber-black/50 border pl-10 pr-4 py-2 rounded-lg text-white focus:outline-none transition-all font-mono text-sm",
                            error ? "border-red-500 ring-1 ring-red-500" : "border-cyber-cyan/30 focus:border-cyber-cyan"
                        )}
                        required
                        disabled={isLoading}
                    />
                    {error && (
                        <div className="absolute top-[calc(100%+4px)] left-0 bg-cyber-black border border-red-500/50 p-2 rounded-md shadow-lg z-[100] min-w-[200px]">
                            <div className="flex items-center gap-2 text-red-500 text-[10px] font-mono">
                                <AlertTriangle className="w-3 h-3" />
                                {error}
                            </div>
                        </div>
                    )}
                </div>
                <NeonButton
                    type="submit"
                    className="px-6 py-2 text-xs"
                    disabled={isLoading}
                >
                    {isLoading ? "SYNCING..." : "RE-PROCESS"}
                </NeonButton>
            </form>
        );
    }

    return (
        <GlassCard className="w-full max-w-2xl mx-auto" variant="cyan">
            <form onSubmit={handleSubmit} className="space-y-6">
                <div className="space-y-2">
                    <label className="text-cyber-cyan text-xs font-bold uppercase tracking-widest flex items-center gap-2">
                        <LinkIcon className="w-3 h-3" /> Video Source URL
                    </label>
                    <input
                        type="text"
                        value={videoUrl}
                        onChange={(e) => {
                            setVideoUrl(e.target.value);
                            if (error) setError(null);
                        }}
                        placeholder="https://www.youtube.com/watch?v=..."
                        className={cn(
                            "w-full bg-cyber-black/50 border p-3 rounded-lg text-white focus:outline-none transition-all font-mono text-sm",
                            error ? "border-red-500 ring-1 ring-red-500" : "border-cyber-cyan/30 focus:border-cyber-cyan focus:ring-1 focus:ring-cyber-cyan"
                        )}
                        required
                        disabled={isLoading}
                    />
                    {error && (
                        <motion.div
                            initial={{ opacity: 0, y: -5 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="flex items-center gap-2 text-red-500 text-[10px] font-mono mt-1"
                        >
                            <AlertTriangle className="w-3 h-3" />
                            {error}
                        </motion.div>
                    )}
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                        <label className="text-cyber-magenta text-xs font-bold uppercase tracking-widest flex items-center gap-2">
                            <User className="w-3 h-3" /> Client Identifier
                        </label>
                        <input
                            type="text"
                            value={clientId}
                            onChange={(e) => setClientId(e.target.value)}
                            className="w-full bg-cyber-black/50 border border-cyber-magenta/30 p-3 rounded-lg text-white focus:outline-none focus:border-cyber-magenta transition-all font-mono text-sm"
                            disabled={isLoading}
                        />
                    </div>

                    <div className="space-y-2">
                        <label className="text-cyber-yellow text-xs font-bold uppercase tracking-widest flex items-center gap-2">
                            <Zap className="w-3 h-3" /> Tone Profile
                        </label>
                        <select
                            value={toneProfile}
                            onChange={(e) => setToneProfile(e.target.value)}
                            className="w-full bg-cyber-black/50 border border-cyber-yellow/30 p-3 rounded-lg text-white focus:outline-none focus:border-cyber-yellow transition-all font-mono text-sm appearance-none"
                            disabled={isLoading}
                        >
                            <option value="professional">Professional</option>
                            <option value="educational">Educational</option>
                            <option value="aggressive">Aggressive</option>
                            <option value="empathetic">Empathetic</option>
                            <option value="inspirational">Inspirational</option>
                        </select>
                    </div>
                </div>

                <div className="space-y-3">
                    <div className="flex items-center justify-between">
                        <label className="text-white/50 text-[10px] font-mono uppercase tracking-widest">
                            Target Platforms
                        </label>
                        <button
                            type="button"
                            onClick={() => setSelectedPlatforms(
                                selectedPlatforms.length === PLATFORMS.length ? [] : PLATFORMS.map(p => p.id)
                            )}
                            className="text-[9px] font-mono text-cyber-cyan/60 hover:text-cyber-cyan transition-colors uppercase"
                        >
                            {selectedPlatforms.length === PLATFORMS.length ? "Clear All" : "Select All"}
                        </button>
                    </div>
                    <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                        {PLATFORMS.map((platform) => {
                            const isSelected = selectedPlatforms.includes(platform.id);
                            return (
                                <motion.button
                                    key={platform.id}
                                    type="button"
                                    onClick={() => togglePlatform(platform.id)}
                                    disabled={isLoading}
                                    whileHover={{ scale: 1.03 }}
                                    whileTap={{ scale: 0.97 }}
                                    transition={{ type: "spring", stiffness: 500, damping: 25 }}
                                    className={cn(
                                        "relative flex items-center gap-2 px-3 py-2 rounded-lg border cursor-pointer select-none",
                                        isSelected
                                            ? "bg-white/10 border-white/25"
                                            : "bg-transparent border-white/10 hover:border-white/20"
                                    )}
                                >
                                    {/* Soft glow - always visible, just dimmer when not selected */}
                                    <div className={cn(
                                        "absolute inset-0 rounded-lg opacity-10 blur-md transition-opacity duration-150",
                                        isSelected ? platform.color.replace("text-", "bg-") : "bg-transparent"
                                    )} />

                                    {/* Indicator dot with instant color change */}
                                    <div className={cn(
                                        "w-2 h-2 rounded-full shrink-0 transition-all duration-100",
                                        isSelected
                                            ? cn(platform.color.replace("text-", "bg-"), "shadow-[0_0_6px_currentColor]")
                                            : "bg-white/20"
                                    )} />

                                    {/* Label */}
                                    <span className={cn(
                                        "text-[10px] font-semibold uppercase tracking-wide transition-colors duration-100",
                                        isSelected ? "text-white" : "text-white/50"
                                    )}>
                                        {platform.label}
                                    </span>

                                    {/* Quick checkmark */}
                                    <div className={cn(
                                        "ml-auto transition-all duration-100",
                                        isSelected ? "opacity-100 scale-100" : "opacity-0 scale-75"
                                    )}>
                                        <svg className="w-3 h-3 text-cyber-green" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                                        </svg>
                                    </div>
                                </motion.button>
                            );
                        })}
                    </div>
                </div>

                <NeonButton
                    type="submit"
                    className="w-full py-4 text-lg"
                    disabled={isLoading || !videoUrl}
                >
                    {isLoading ? "INITIALIZING NEURAL LINK..." : "EXECUTE REPURPOSING ENGINE"}
                </NeonButton>
            </form>
        </GlassCard>
    );
}
