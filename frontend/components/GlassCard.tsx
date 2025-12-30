import { cn } from "@/lib/utils";
import { ReactNode } from "react";

interface GlassCardProps {
    children: ReactNode;
    className?: string;
    variant?: "cyan" | "magenta" | "blue";
}

export function GlassCard({ children, className, variant = "cyan" }: GlassCardProps) {
    const variantClasses = {
        cyan: "neon-border-cyan",
        magenta: "neon-border-magenta",
        blue: "border-cyber-blue shadow-[0_0_10px_rgba(0,128,255,0.5)]",
    };

    return (
        <div className={cn(
            "glass-card p-6 rounded-xl relative overflow-hidden",
            variantClasses[variant],
            className
        )}>
            {/* Decorative corner */}
            <div className={cn(
                "absolute top-0 right-0 w-8 h-8 border-t-2 border-r-2",
                variant === "cyan" ? "border-cyber-cyan" : "border-cyber-magenta"
            )} />
            {children}
        </div>
    );
}
