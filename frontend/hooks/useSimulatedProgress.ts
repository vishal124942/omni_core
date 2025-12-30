"use client";

import { useState, useEffect, useRef } from "react";

/**
 * Custom hook to simulate progress during long-running operations.
 * Progress increments smoothly up to a cap, then jumps to 100% when marked complete.
 */
export function useSimulatedProgress(
    isActive: boolean,
    onComplete: boolean,
    options: {
        incrementPerMs?: number;  // % to add per millisecond
        maxProgress?: number;     // Cap before completion (e.g., 95%)
        intervalMs?: number;      // Update interval
    } = {}
) {
    const {
        incrementPerMs = 0.05,   // ~5% per 100ms = ~50% over 1 second
        maxProgress = 95,
        intervalMs = 100
    } = options;

    const [progress, setProgress] = useState(0);
    const intervalRef = useRef<NodeJS.Timeout | null>(null);

    useEffect(() => {
        if (isActive && !onComplete) {
            // Start simulating progress
            setProgress(5); // Start at 5%

            intervalRef.current = setInterval(() => {
                setProgress(prev => {
                    const newProgress = prev + (incrementPerMs * intervalMs);
                    return Math.min(newProgress, maxProgress);
                });
            }, intervalMs);
        } else if (onComplete) {
            // Task completed - jump to 100%
            if (intervalRef.current) {
                clearInterval(intervalRef.current);
                intervalRef.current = null;
            }
            setProgress(100);
        } else {
            // Not active - reset
            if (intervalRef.current) {
                clearInterval(intervalRef.current);
                intervalRef.current = null;
            }
            setProgress(0);
        }

        return () => {
            if (intervalRef.current) {
                clearInterval(intervalRef.current);
            }
        };
    }, [isActive, onComplete, incrementPerMs, maxProgress, intervalMs]);

    return progress;
}

/**
 * Hook to manage simulated progress for multiple steps.
 * Returns a map of step ID -> progress percentage.
 */
export function useMultiStepProgress(
    steps: Array<{ id: string; status: "pending" | "active" | "completed" }>,
    options: {
        incrementPerMs?: number;
        maxProgress?: number;
        intervalMs?: number;
    } = {}
) {
    const {
        incrementPerMs = 0.03,  // Slower increment for multi-step
        maxProgress = 90,
        intervalMs = 100
    } = options;

    const [progressMap, setProgressMap] = useState<Record<string, number>>({});
    const intervalsRef = useRef<Record<string, NodeJS.Timeout>>({});

    useEffect(() => {
        steps.forEach(step => {
            const currentProgress = progressMap[step.id] || 0;

            if (step.status === "active" && !intervalsRef.current[step.id]) {
                // Start progress for this step
                setProgressMap(prev => ({ ...prev, [step.id]: 5 }));

                intervalsRef.current[step.id] = setInterval(() => {
                    setProgressMap(prev => {
                        const current = prev[step.id] || 5;
                        const next = Math.min(current + (incrementPerMs * intervalMs), maxProgress);
                        return { ...prev, [step.id]: Math.round(next) };
                    });
                }, intervalMs);
            } else if (step.status === "completed") {
                // Complete this step
                if (intervalsRef.current[step.id]) {
                    clearInterval(intervalsRef.current[step.id]);
                    delete intervalsRef.current[step.id];
                }
                if (currentProgress !== 100) {
                    setProgressMap(prev => ({ ...prev, [step.id]: 100 }));
                }
            } else if (step.status === "pending") {
                // Reset this step
                if (intervalsRef.current[step.id]) {
                    clearInterval(intervalsRef.current[step.id]);
                    delete intervalsRef.current[step.id];
                }
                if (currentProgress !== 0) {
                    setProgressMap(prev => ({ ...prev, [step.id]: 0 }));
                }
            }
        });

        return () => {
            Object.values(intervalsRef.current).forEach(clearInterval);
        };
    }, [steps, incrementPerMs, maxProgress, intervalMs]);

    return progressMap;
}
