import { cn } from "@/lib/utils";
import { ButtonHTMLAttributes } from "react";

interface NeonButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
    variant?: "cyan" | "magenta";
    glow?: boolean;
}

export function NeonButton({
    children,
    className,
    variant = "cyan",
    glow = true,
    ...props
}: NeonButtonProps) {
    const variants = {
        cyan: "bg-cyber-cyan/10 border-cyber-cyan text-cyber-cyan hover:bg-cyber-cyan hover:text-cyber-black",
        magenta: "bg-cyber-magenta/10 border-cyber-magenta text-cyber-magenta hover:bg-cyber-magenta hover:text-cyber-black",
    };

    return (
        <button
            className={cn(
                "px-6 py-2 border font-bold uppercase tracking-widest transition-all duration-300 relative group",
                variants[variant],
                glow && (variant === "cyan" ? "shadow-[0_0_15px_rgba(0,245,255,0.3)]" : "shadow-[0_0_15px_rgba(255,0,255,0.3)]"),
                className
            )}
            {...props}
        >
            <span className="relative z-10">{children}</span>
            {/* Hover background effect */}
            <div className={cn(
                "absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-300",
                variant === "cyan" ? "bg-cyber-cyan" : "bg-cyber-magenta"
            )} />
        </button>
    );
}
