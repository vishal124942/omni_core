"use client";

import React, { useEffect, useRef, useState } from 'react';
import { Terminal, Trash2, Power } from 'lucide-react';
import { cn } from '@/lib/utils';

interface LogConsoleProps {
    className?: string;
}

export function LogConsole({ className }: LogConsoleProps) {
    const [logs, setLogs] = useState<string[]>([]);
    const [isConnected, setIsConnected] = useState(false);
    const scrollRef = useRef<HTMLDivElement>(null);
    const wsRef = useRef<WebSocket | null>(null);

    useEffect(() => {
        const connect = () => {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//localhost:8000/ws/logs`;

            const ws = new WebSocket(wsUrl);
            wsRef.current = ws;

            ws.onopen = () => {
                setIsConnected(true);
                addLog(">>> SYSTEM: NEURAL LINK ESTABLISHED. STREAMING LOGS...");
            };

            ws.onmessage = (event) => {
                addLog(event.data);
            };

            ws.onclose = () => {
                setIsConnected(false);
                addLog(">>> SYSTEM: NEURAL LINK SEVERED. RETRYING...");
                setTimeout(connect, 3000);
            };

            ws.onerror = () => {
                setIsConnected(false);
            };
        };

        connect();

        return () => {
            if (wsRef.current) {
                wsRef.current.close();
            }
        };
    }, []);

    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [logs]);

    const addLog = (message: string) => {
        setLogs((prev) => [...prev.slice(-100), message]);
    };

    const clearLogs = () => {
        setLogs([]);
    };

    return (
        <div className={cn(
            "relative flex flex-col h-64 bg-cyber-black/80 border border-cyber-cyan/30 rounded-lg overflow-hidden glass-card",
            className
        )}>
            {/* Console Header */}
            <div className="flex items-center justify-between px-4 py-2 bg-cyber-cyan/10 border-b border-cyber-cyan/30">
                <div className="flex items-center gap-2">
                    <Terminal className="w-4 h-4 text-cyber-cyan" />
                    <span className="text-xs font-mono font-bold text-cyber-cyan uppercase tracking-widest">
                        System Log Console
                    </span>
                    <div className={cn(
                        "w-2 h-2 rounded-full animate-pulse",
                        isConnected ? "bg-cyber-green shadow-[0_0_8px_#00ff9f]" : "bg-cyber-red shadow-[0_0_8px_#ff003c]"
                    )} />
                </div>
                <div className="flex items-center gap-3">
                    <button
                        onClick={clearLogs}
                        className="text-cyber-cyan/50 hover:text-cyber-cyan transition-colors"
                        title="Clear Logs"
                    >
                        <Trash2 className="w-4 h-4" />
                    </button>
                    <div className="flex gap-1">
                        <div className="w-2 h-2 rounded-full bg-cyber-red/50" />
                        <div className="w-2 h-2 rounded-full bg-cyber-yellow/50" />
                        <div className="w-2 h-2 rounded-full bg-cyber-green/50" />
                    </div>
                </div>
            </div>

            {/* Console Body */}
            <div
                ref={scrollRef}
                className="flex-1 p-4 font-mono text-xs overflow-y-auto scrollbar-thin scrollbar-thumb-cyber-cyan/30 scrollbar-track-transparent"
            >
                {logs.length === 0 ? (
                    <div className="text-cyber-cyan/30 italic">Waiting for system logs...</div>
                ) : (
                    logs.map((log, i) => (
                        <div key={i} className={cn(
                            "mb-1 break-all",
                            log.includes("ERROR") ? "text-cyber-red" :
                                log.includes("WARNING") ? "text-cyber-yellow" :
                                    log.includes(">>> SYSTEM") ? "text-cyber-magenta font-bold" :
                                        "text-cyber-cyan/80"
                        )}>
                            <span className="opacity-50 mr-2">[{new Date().toLocaleTimeString()}]</span>
                            {log}
                        </div>
                    ))
                )}
            </div>

            {/* Scanline Effect for Console */}
            <div className="absolute inset-0 pointer-events-none bg-[linear-gradient(rgba(18,16,16,0)_50%,rgba(0,0,0,0.1)_50%),linear-gradient(90deg,rgba(255,0,0,0.03),rgba(0,255,0,0.01),rgba(0,0,255,0.03))] bg-[length:100%_4px,3px_100%] opacity-20" />
        </div>
    );
}
