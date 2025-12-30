"use client";

import { useState, useEffect, useMemo } from "react";
import { HeroSection } from "@/components/HeroSection";
import { VideoInputForm } from "@/components/VideoInputForm";
import { PipelineTracker, PipelineStep, StepStatus } from "@/components/PipelineTracker";
import { ContentDisplay } from "@/components/ContentDisplay";
import { LogConsole } from "@/components/LogConsole";
import { AutoSidebar } from "@/components/AutoSidebar";
import { ThinkingIndicator } from "@/components/ThinkingIndicator";
import { useMultiStepProgress } from "@/hooks/useSimulatedProgress";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";
import {
  FileText,
  Brain,
  Share2,
  Scissors,
  Database,
  AlertTriangle,
  Linkedin,
  Twitter,
  Zap,
  Mail,
  Image as ImageIcon,
  Search,
  Volume2,
  Cpu,
  RefreshCcw,
  Layout
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

const INITIAL_STEPS: PipelineStep[] = [
  { id: "transcription", label: "Transcription", description: "Local Whisper", icon: FileText, status: "pending" },
  { id: "analysis", label: "Intelligence", description: "Brain + Research", icon: Cpu, status: "pending" },
  { id: "generation", label: "Content Hub", description: "Social Assets", icon: Share2, status: "pending" },
  { id: "visuals", label: "Visual Studio", description: "Carousel + Thumbnails", icon: Layout, status: "pending" },
  { id: "audio", label: "Audio Hub", description: "Neural Dubbing", icon: Volume2, status: "pending" },
  { id: "storage", label: "Airtable", description: "Production Board", icon: Database, status: "pending" },
];

export default function Home() {
  const [steps, setSteps] = useState<PipelineStep[]>(INITIAL_STEPS);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<any>(null);
  const [activeSection, setActiveSection] = useState("analysis");
  const [realProgress, setRealProgress] = useState<Record<string, number>>({});
  const [selectedPlatforms, setSelectedPlatforms] = useState<string[]>([]);

  // Thinking indicator state
  const [isThinking, setIsThinking] = useState(false);
  const [thinkingStep, setThinkingStep] = useState("");
  const [thinkingLabel, setThinkingLabel] = useState("");
  const [thinkingText, setThinkingText] = useState("");

  // Persist result to localStorage
  useEffect(() => {
    const savedResult = localStorage.getItem("omnicore_result");
    const savedSteps = localStorage.getItem("omnicore_steps");
    const savedPlatforms = localStorage.getItem("omnicore_platforms");

    if (savedResult) {
      try {
        setResult(JSON.parse(savedResult));
        if (savedSteps) {
          setSteps(JSON.parse(savedSteps));
        }
        if (savedPlatforms) {
          setSelectedPlatforms(JSON.parse(savedPlatforms));
        }
      } catch (e) {
        console.error("Failed to restore saved state");
      }
    }
  }, []);

  // Save result to localStorage when it changes
  useEffect(() => {
    if (result) {
      localStorage.setItem("omnicore_result", JSON.stringify(result));
      localStorage.setItem("omnicore_steps", JSON.stringify(steps));
      localStorage.setItem("omnicore_platforms", JSON.stringify(selectedPlatforms));
    }
  }, [result, steps, selectedPlatforms]);

  // Use simulated progress for visual feedback
  const simulatedProgress = useMultiStepProgress(
    steps.map(s => ({ id: s.id, status: s.status as "pending" | "active" | "completed" })),
    {
      incrementPerMs: 0.05,  // Slightly faster for better feedback
      maxProgress: 90,       // Cap at 90%
      intervalMs: 100
    }
  );

  // Merge real progress (from backend) with simulated progress
  // Ensure we don't jump back to 0 when a step starts
  const stepsWithProgress = useMemo(() => {
    return steps.map(step => {
      const real = realProgress[step.id] || 0;
      const simulated = simulatedProgress[step.id] || 0;

      let progress = 0;
      if (step.status === "completed") {
        progress = 100;
      } else if (step.status === "active") {
        // Use the maximum of real and simulated to ensure smooth upward movement
        progress = Math.max(real, simulated);
      }

      return { ...step, progress: Math.round(progress) };
    });
  }, [steps, realProgress, simulatedProgress]);

  const updateStepStatus = (id: string, status: StepStatus) => {
    setSteps(prev => prev.map(step =>
      step.id === id ? {
        ...step,
        status,
        progress: status === "completed" ? 100 : step.progress
      } : step
    ));
  };

  const resetSteps = async () => {
    // 1. Clear Local Storage
    localStorage.removeItem("omnicore_result");
    localStorage.removeItem("omnicore_steps");
    localStorage.removeItem("omnicore_platforms");

    // 2. Call Backend Reset (Clear Disk)
    try {
      await fetch("http://localhost:8000/reset-project", { method: "POST" });
    } catch (e) {
      console.error("Failed to reset backend data:", e);
    }

    // 3. Reset UI State
    setSteps(INITIAL_STEPS);
    setError(null);
    setResult(null);
    setIsLoading(false);
    setActiveSection("analysis");
    setSelectedPlatforms([]);
    setThinkingStep("");
    setThinkingLabel("");
    setThinkingText("");
    setIsThinking(false);
  };

  const handleStopPipeline = () => {
    // Abort any ongoing fetch
    const controller = (window as any).currentPipelineController;
    if (controller) {
      controller.abort();
    }

    // Reset all state
    setIsLoading(false);
    setIsThinking(false);
    setThinkingText("");
    setThinkingStep("");
    setThinkingLabel("");
    setError("Pipeline stopped by user");
    setSteps(prev => prev.map(step =>
      step.status === "active" ? { ...step, status: "pending" } : step
    ));
  };

  const handleSectionClick = (id: string) => {
    setActiveSection(id);
  };

  const handleProcessVideo = async (data: {
    videoUrl: string;
    clientId: string;
    toneProfile: string;
    platforms: string[];
  }) => {
    setIsLoading(true);
    // Reset state with smart skipping
    setError(null);
    localStorage.removeItem("omnicore_result");
    localStorage.removeItem("omnicore_steps");

    const smartSteps = INITIAL_STEPS.map(step => {
      if (step.id === "transcription" || step.id === "analysis" || step.id === "storage") return step;

      if (step.id === "generation") {
        const hasGen = ["twitter", "blog", "linkedin", "newsletter"].some(p => data.platforms.includes(p));
        return hasGen ? step : { ...step, status: "skipped" as StepStatus };
      }
      if (step.id === "visuals") {
        return data.platforms.includes("visuals") ? step : { ...step, status: "skipped" as StepStatus };
      }
      if (step.id === "audio") {
        return data.platforms.includes("audio") ? step : { ...step, status: "skipped" as StepStatus };
      }
      return step;
    });
    setSteps(smartSteps);
    setSelectedPlatforms(data.platforms);

    setActiveSection("analysis");

    // Initialize empty result structure
    setResult({
      analysis: undefined,
      linkedin_post: undefined,
      twitter_thread: undefined,
      blog_post: undefined,
      linkedin_hooks: [],
      broll_images: [],
      seo_score: undefined,
      newsletter_html: undefined
    });

    const controller = new AbortController();
    (window as any).currentPipelineController = controller;

    try {
      updateStepStatus("transcription", "active");

      // Pass platforms to the streaming backend
      // We also pass the platforms in a way the backend expects
      const response = await api.processVideoStream(
        data.videoUrl,
        data.clientId,
        data.toneProfile,
        data.platforms
      );

      if (!response.body) throw new Error("No response body");

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");

        // Process all complete lines
        buffer = lines.pop() || ""; // Keep the last partial line in buffer

        for (const line of lines) {
          if (!line.trim()) continue;

          try {
            const event = JSON.parse(line);

            // Handle different event types
            switch (event.type) {
              case "status":
                console.log("Status:", event.message);
                break;

              case "progress":
                console.log("Progress:", event.step, event.percent);
                setRealProgress(prev => ({ ...prev, [event.step]: event.percent }));
                break;

              case "thinking_start":
                setIsThinking(true);
                setThinkingStep(event.step);
                setThinkingLabel(event.label);
                setThinkingText("");
                break;

              case "thinking":
                setThinkingText(prev => prev + event.token);
                break;

              case "thinking_done":
                setIsThinking(false);
                break;

              case "transcript":
                updateStepStatus("transcription", "completed");
                updateStepStatus("analysis", "active");
                break;

              case "analysis":
                setResult((prev: any) => ({ ...prev, analysis: event.data }));
                updateStepStatus("analysis", "active");
                setActiveSection("analysis");
                break;

              case "research":
                setResult((prev: any) => ({ ...prev, research: event.data }));
                updateStepStatus("analysis", "completed");
                updateStepStatus("generation", "active");
                setActiveSection("research");
                break;
                break;

              case "linkedin":
                setResult((prev: any) => ({ ...prev, linkedin_post: event.data }));
                setActiveSection("linkedin");
                break;

              case "twitter":
                setResult((prev: any) => ({ ...prev, twitter_thread: event.data }));
                setActiveSection("twitter");
                break;

              case "blog":
                setResult((prev: any) => ({ ...prev, blog_post: event.data }));
                setActiveSection("blog");
                break;

              case "hooks":
                setResult((prev: any) => ({ ...prev, linkedin_hooks: event.data }));
                setActiveSection("hooks");
                break;

              case "broll":
                setResult((prev: any) => ({ ...prev, broll_images: event.data }));
                updateStepStatus("features", "active");
                break;

              case "seo":
                setResult((prev: any) => ({ ...prev, seo_score: event.data }));
                break;

              case "newsletter":
                setResult((prev: any) => ({ ...prev, newsletter_html: event.data }));
                setActiveSection("newsletter");
                break;

              case "carousel":
                setResult((prev: any) => ({ ...prev, carousel: event.data }));
                updateStepStatus("generation", "completed");
                updateStepStatus("visuals", "active");
                setActiveSection("carousel");
                break;

              case "thumbnails":
                setResult((prev: any) => ({ ...prev, thumbnails: event.data }));
                setActiveSection("thumbnails");
                break;

              case "audio":
                setResult((prev: any) => ({ ...prev, audio: event.data }));
                updateStepStatus("visuals", "completed");
                updateStepStatus("audio", "active");
                setActiveSection("audio");
                break;
                break;

              case "airtable":
                updateStepStatus("generation", "completed");
                updateStepStatus("features", "completed");
                updateStepStatus("storage", "completed");
                break;

              case "error":
                setError(event.error);
                setIsLoading(false);
                return;
            }
          } catch (e) {
            console.error("Error parsing stream line:", e);
          }
        }
      }

      // Mark all as complete if no error
      setSteps(prev => prev.map(step => ({ ...step, status: "completed" })));

    } catch (err: any) {
      setError(err.toString());
      // Mark current active step as error
      setSteps(prev => prev.map(step =>
        step.status === "active" ? { ...step, status: "error" } : step
      ));
    } finally {
      setIsLoading(false);
    }
  };

  // Content section sidebar steps with simulated progress
  const getSidebarProgress = (status: string) => {
    if (status === "completed") return 100;
    if (status === "active") return simulatedProgress["generation"] || 50;
    return 0;
  };

  const sidebarSteps = [
    { id: "analysis", label: "Insight", icon: Brain, status: result?.analysis ? "completed" : isLoading ? "active" : "pending", progress: result?.analysis ? 100 : simulatedProgress["analysis"] || 0 },
    { id: "research", label: "Research", icon: Search, status: result?.research ? "completed" : result?.analysis ? "active" : "pending", progress: result?.research ? 100 : (result?.analysis ? simulatedProgress["analysis"] || 30 : 0) },
    { id: "linkedin", label: "LinkedIn", icon: Linkedin, status: result?.linkedin_post ? "completed" : result?.research ? "active" : "pending", progress: result?.linkedin_post ? 100 : (result?.research ? simulatedProgress["generation"] || 30 : 0) },
    { id: "twitter", label: "Twitter", icon: Twitter, status: result?.twitter_thread?.length > 0 ? "completed" : result?.linkedin_post ? "active" : "pending", progress: result?.twitter_thread?.length > 0 ? 100 : (result?.linkedin_post ? simulatedProgress["generation"] || 30 : 0) },
    { id: "blog", label: "Blog", icon: FileText, status: result?.blog_post ? "completed" : result?.twitter_thread?.length > 0 ? "active" : "pending", progress: result?.blog_post ? 100 : (result?.twitter_thread?.length > 0 ? simulatedProgress["generation"] || 30 : 0) },
    { id: "newsletter", label: "Newsletter", icon: Mail, status: result?.newsletter_html ? "completed" : result?.blog_post ? "active" : "pending", progress: result?.newsletter_html ? 100 : (result?.blog_post ? simulatedProgress["generation"] || 30 : 0) },
    { id: "carousel", label: "Carousel", icon: Layout, status: result?.carousel ? "completed" : result?.newsletter_html ? "active" : "pending", progress: result?.carousel ? 100 : (result?.newsletter_html ? simulatedProgress["visuals"] || 30 : 0) },
    { id: "thumbnails", label: "Thumbnails", icon: ImageIcon, status: result?.thumbnails ? "completed" : result?.carousel ? "active" : "pending", progress: result?.thumbnails ? 100 : (result?.carousel ? simulatedProgress["visuals"] || 30 : 0) },
    { id: "audio", label: "Audio", icon: Volume2, status: result?.audio ? "completed" : result?.thumbnails ? "active" : "pending", progress: result?.audio ? 100 : (result?.thumbnails ? simulatedProgress["audio"] || 30 : 0) },
  ].filter(step => {
    // Always show core steps
    if (["analysis", "research"].includes(step.id)) return true;

    // For specific content types, check if they were selected
    if (selectedPlatforms.length > 0) {
      if (step.id === "linkedin" && !selectedPlatforms.includes("linkedin")) return false;
      if (step.id === "twitter" && !selectedPlatforms.includes("twitter")) return false;
      if (step.id === "blog" && !selectedPlatforms.includes("blog")) return false;
      if (step.id === "newsletter" && !selectedPlatforms.includes("newsletter")) return false;
      if (step.id === "carousel" && !selectedPlatforms.includes("visuals")) return false;
      if (step.id === "thumbnails" && !selectedPlatforms.includes("visuals")) return false;
      if (step.id === "audio" && !selectedPlatforms.includes("audio")) return false;
    }
    return true;
  }) as any[];

  const isDashboardMode = isLoading || result;

  return (
    <div className={cn(
      "relative transition-all duration-500",
      isDashboardMode ? "h-screen overflow-hidden bg-cyber-black" : "pb-20"
    )}>
      <AnimatePresence>
        {isDashboardMode && (
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            className="fixed left-0 top-0 h-full z-50"
          >
            <AutoSidebar
              steps={sidebarSteps}
              activeSection={activeSection}
              onSectionClick={handleSectionClick}
              isBotActive={isLoading}
            />
          </motion.div>
        )}
      </AnimatePresence>

      <div className={cn(
        "transition-all duration-500",
        isDashboardMode ? "pl-72 h-full flex flex-col" : "container mx-auto"
      )}>
        {!isDashboardMode && <HeroSection />}

        <div className={cn(
          "transition-all duration-500",
          isDashboardMode ? "p-8 flex-1 flex flex-col overflow-hidden" : "space-y-12"
        )}>
          {/* Header area in Dashboard Mode */}
          {isDashboardMode && (
            <div className="flex justify-between items-center mb-8">
              <div className="flex items-center gap-4">
                <div className="w-10 h-10 bg-cyber-cyan/20 rounded-lg flex items-center justify-center border border-cyber-cyan/30">
                  <Zap className="w-6 h-6 text-cyber-cyan" />
                </div>
                <div>
                  <h1 className="text-xl font-bold text-white uppercase tracking-tighter">Autonomous Agent</h1>
                  <p className="text-[10px] text-white/40 font-mono uppercase tracking-widest">Neural Link: Active</p>
                </div>
              </div>
              <div className="max-w-md flex-1 mx-8 flex items-center gap-3">
                <VideoInputForm onSubmit={handleProcessVideo} isLoading={isLoading} variant="minimal" />
                {isLoading && (
                  <motion.button
                    onClick={handleStopPipeline}
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    className="flex items-center gap-2 px-4 py-2 bg-cyber-red/20 hover:bg-cyber-red/30 border border-cyber-red/40 rounded-lg text-[10px] font-mono text-cyber-red uppercase tracking-wide transition-all whitespace-nowrap"
                  >
                    <motion.div
                      animate={{ opacity: [1, 0.5, 1] }}
                      transition={{ duration: 1, repeat: Infinity }}
                      className="w-2 h-2 bg-cyber-red rounded-sm"
                    />
                    Stop
                  </motion.button>
                )}
                <motion.button
                  onClick={resetSteps}
                  disabled={isLoading}
                  whileHover={{ scale: 1.03, backgroundColor: "rgba(0, 245, 255, 0.1)" }}
                  whileTap={{ scale: 0.97 }}
                  className="flex items-center gap-2 px-4 py-2 bg-white/5 hover:bg-cyber-cyan/10 border border-white/10 hover:border-cyber-cyan/30 rounded-lg text-[10px] font-mono text-white/60 hover:text-cyber-cyan uppercase tracking-wide transition-all whitespace-nowrap disabled:opacity-30 disabled:pointer-events-none"
                >
                  <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                  </svg>
                  New
                </motion.button>
              </div>
              <div className="flex gap-3 items-center">
                {stepsWithProgress.map((step) => (
                  <div
                    key={step.id}
                    className="flex items-center gap-1"
                    title={`${step.label}: ${step.progress || (step.status === "completed" ? 100 : 0)}%`}
                  >
                    <div
                      className={cn(
                        "w-2 h-2 rounded-full transition-all duration-500 shrink-0",
                        step.status === "completed" ? "bg-cyber-green shadow-[0_0_10px_#39ff14]" :
                          step.status === "active" ? "bg-cyber-cyan animate-pulse shadow-[0_0_10px_#00f5ff]" :
                            "bg-white/10"
                      )}
                    />
                    {step.status === "active" && (
                      <div className="w-12 h-1 bg-white/10 rounded-full overflow-hidden">
                        <motion.div
                          initial={{ width: 0 }}
                          animate={{ width: `${step.progress || 0}%` }}
                          transition={{ duration: 0.3 }}
                          className="h-full bg-cyber-cyan"
                        />
                      </div>
                    )}
                    {step.status === "completed" && (
                      <span className="text-[8px] font-mono text-cyber-green">✓</span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {!isDashboardMode && <VideoInputForm onSubmit={handleProcessVideo} isLoading={isLoading} />}

          {(isLoading || result || error) && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className={cn(
                "flex-1 flex flex-col overflow-hidden",
                !isDashboardMode && "space-y-8"
              )}
            >
              {/* Thinking Indicator - Real-time LLM streaming */}
              <div className="z-10 mb-6 max-w-3xl mx-auto w-full px-4 pointer-events-none">
                <ThinkingIndicator
                  isVisible={isThinking}
                  currentStep={thinkingStep}
                  stepLabel={thinkingLabel}
                  streamingText={thinkingText}
                />
              </div>

              {/* Pipeline Tracker & Log Console only in non-dashboard or as small elements */}
              {!isDashboardMode && (
                <>
                  <div className="mb-12">
                    <PipelineTracker steps={stepsWithProgress} />
                  </div>
                  <div className="mb-12">
                    <LogConsole />
                  </div>
                </>
              )}

              {/* Error Message */}
              <AnimatePresence>
                {error && (
                  <motion.div
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className="max-w-2xl mx-auto p-4 bg-cyber-red/10 border border-cyber-red/50 rounded-lg flex items-center gap-4 text-cyber-red mb-8"
                  >
                    <AlertTriangle className="w-6 h-6 shrink-0" />
                    <div className="font-mono text-sm">
                      <p className="font-bold uppercase tracking-widest">System Failure</p>
                      <p>{error}</p>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>

              {/* Main Content Area */}
              {result && (
                <div className={cn(
                  "flex-1 overflow-hidden",
                  isDashboardMode ? "relative" : "mt-12"
                )}>
                  <ContentDisplay content={result} activeSection={activeSection} />
                </div>
              )}
            </motion.div>
          )}
        </div>

        {!isDashboardMode && (
          <div className="mt-20 text-center text-white/20 font-mono text-[10px] uppercase tracking-[0.3em]">
            Neural Link Established // Secure Connection // End-to-End Encryption
          </div>
        )}
      </div>
    </div>
  );
}
