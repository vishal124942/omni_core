"use client";

import { motion } from "framer-motion";

export function HeroSection() {
    return (
        <div className="relative py-20 flex flex-col items-center justify-center text-center">
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8 }}
                className="relative"
            >
                <h1 className="text-6xl md:text-8xl font-black tracking-tighter mb-4 relative z-10">
                    <span className="animate-glitch inline-block text-white">OMNI</span>
                    <span className="text-cyber-cyan neon-text-cyan mx-4">CORE</span>
                </h1>
                <div className="absolute -inset-2 bg-cyber-cyan/20 blur-2xl rounded-full z-0" />
            </motion.div>

            <motion.p
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.5, duration: 1 }}
                className="text-cyber-magenta font-mono tracking-widest uppercase text-sm md:text-base mb-8"
            >
        // AI CONTENT REPURPOSING ENGINE _ v1.0.0
            </motion.p>

            <div className="w-full max-w-2xl h-px bg-gradient-to-r from-transparent via-cyber-cyan to-transparent opacity-50 mb-12" />
        </div>
    );
}
