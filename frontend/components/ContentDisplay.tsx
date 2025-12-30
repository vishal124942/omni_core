"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { GlassCard } from "./GlassCard";
import ReactMarkdown from "react-markdown";
import {
    BarChart3,
    Linkedin,
    Twitter,
    FileText,
    Mail,
    Zap,
    Image,
    Copy,
    CheckCircle2,
    Award,
    Search,
    Layout,
    Volume2,
    Download,
    ExternalLink,
    ShieldCheck,
    TrendingUp,
    Play,
    Pause,
    RefreshCcw,
    Image as ImageIcon,
    ChevronLeft,
    ChevronRight,
    FileDown
} from "lucide-react";
import { cn } from "@/lib/utils";

interface ContentDisplayProps {
    content: {
        analysis?: {
            big_idea: string;
            strong_takes: string[];
            tone: string;
        };
        linkedin_post?: string;
        twitter_thread?: string[];
        blog_post?: string;
        linkedin_hooks?: Array<{
            framework: string;
            hook: string;
            description?: string;
        }>;
        broll_images?: Array<{
            strong_take: string;
            keyword: string;
            image_url: string;
            photographer?: string;
        }>;
        seo_score?: {
            score: number;
            max_score: number;
            grade: string;
            feedback: string[];
        };
        newsletter_html?: string;
        research?: {
            trend_context: string;
            fact_checks: Array<{
                claim: string;
                verdict: string;
                explanation: string;
            }>;
        };
        carousel?: {
            pdf: string;
            images: string[];
        };
        thumbnails?: Array<string>; // Paths or URLs
        audio?: {
            path: string;
            lang: string;
            error?: string;
        };
    };
    activeSection: string;
}

const API_BASE_URL = "http://localhost:8000";

// Style metadata for display
const CAROUSEL_STYLES = {
    cyberpunk: { label: "Cyberpunk", color: "cyan" },
    minimalist: { label: "Minimalist", color: "white" },
    corporate: { label: "Corporate", color: "purple" }
} as const;

type CarouselVariant = { pdf: string; images: string[]; error?: string };
type CarouselData = { variants?: Record<string, CarouselVariant>; default_style?: string } | CarouselVariant;

const CarouselPreview = ({ carousel }: { carousel?: CarouselData }) => {
    const [currentIndex, setCurrentIndex] = useState(0);
    const [selectedStyle, setSelectedStyle] = useState<string>("cyberpunk");

    // Handle both old format (single carousel) and new format (variants)
    const isMultiVariant = carousel && "variants" in carousel;
    const variants = isMultiVariant ? carousel.variants : null;
    const currentVariant: CarouselVariant | undefined = isMultiVariant
        ? variants?.[selectedStyle]
        : (carousel as CarouselVariant | undefined);

    // Reset slide index when changing styles
    useEffect(() => {
        setCurrentIndex(0);
    }, [selectedStyle]);

    if (!carousel || (!isMultiVariant && (!currentVariant?.images || currentVariant.images.length === 0))) {
        return (
            <GlassCard variant="cyan" className="min-h-[400px] flex flex-col items-center justify-center p-0 overflow-hidden">
                <div className="flex flex-col items-center gap-4 py-20">
                    <RefreshCcw className="w-10 h-10 text-cyber-cyan animate-spin opacity-20" />
                    <div className="text-white/20 font-mono uppercase tracking-widest">
                        // BUILDING PDF CAROUSEL...
                    </div>
                </div>
            </GlassCard>
        );
    }

    if (!currentVariant?.images || currentVariant.images.length === 0) {
        return (
            <GlassCard variant="cyan" className="min-h-[400px] flex flex-col items-center justify-center p-0 overflow-hidden">
                <div className="flex flex-col items-center gap-4 py-20">
                    <RefreshCcw className="w-10 h-10 text-cyber-cyan animate-spin opacity-20" />
                    <div className="text-white/20 font-mono uppercase tracking-widest">
                        // LOADING {selectedStyle.toUpperCase()} STYLE...
                    </div>
                </div>
            </GlassCard>
        );
    }

    const nextSlide = () => {
        setCurrentIndex((prev) => (prev + 1) % currentVariant.images.length);
    };

    const prevSlide = () => {
        setCurrentIndex((prev) => (prev - 1 + currentVariant.images.length) % currentVariant.images.length);
    };

    return (
        <div className="space-y-4">
            {/* Style Selector Tabs - only show if multi-variant */}
            {isMultiVariant && variants && (
                <div className="flex gap-2 justify-center">
                    {Object.keys(CAROUSEL_STYLES).map((style) => {
                        const styleInfo = CAROUSEL_STYLES[style as keyof typeof CAROUSEL_STYLES];
                        const isActive = selectedStyle === style;
                        const hasData = variants[style] && !variants[style].error;

                        return (
                            <motion.button
                                key={style}
                                onClick={() => hasData && setSelectedStyle(style)}
                                whileHover={{ scale: hasData ? 1.05 : 1 }}
                                whileTap={{ scale: hasData ? 0.95 : 1 }}
                                disabled={!hasData}
                                className={cn(
                                    "px-4 py-2 rounded-lg text-[10px] font-bold uppercase tracking-wide transition-all duration-150",
                                    isActive
                                        ? "bg-white/15 border border-white/30 text-white shadow-lg"
                                        : hasData
                                            ? "bg-transparent border border-white/10 text-white/50 hover:border-white/20 hover:text-white/70"
                                            : "bg-transparent border border-white/5 text-white/20 cursor-not-allowed"
                                )}
                            >
                                <span className={cn(
                                    "inline-block w-2 h-2 rounded-full mr-2",
                                    styleInfo.color === "cyan" && "bg-cyber-cyan",
                                    styleInfo.color === "white" && "bg-white",
                                    styleInfo.color === "purple" && "bg-purple-500"
                                )} />
                                {styleInfo.label}
                            </motion.button>
                        );
                    })}
                </div>
            )}

            <div className="flex justify-between items-center">
                <h3 className="text-cyber-cyan font-bold uppercase tracking-widest text-sm flex items-center gap-2">
                    <Layout className="w-4 h-4" /> {isMultiVariant ? `${CAROUSEL_STYLES[selectedStyle as keyof typeof CAROUSEL_STYLES]?.label || selectedStyle} Carousel` : "Carousel Preview"}
                </h3>
                <a
                    href={`${API_BASE_URL}${currentVariant.pdf}`}
                    download
                    className="px-4 py-2 bg-cyber-cyan text-cyber-black text-xs font-bold uppercase rounded hover:bg-cyber-cyan/80 transition-colors flex items-center gap-2 shadow-[0_0_15px_rgba(0,243,255,0.3)]"
                >
                    <Download className="w-4 h-4" /> Download PDF
                </a>
            </div>

            <GlassCard variant="cyan" className="p-0 overflow-hidden relative group aspect-square max-w-[500px] mx-auto">
                <AnimatePresence mode="wait">
                    <motion.div
                        key={selectedStyle}
                        initial={{ opacity: 0, x: 50 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0, x: -50 }}
                        transition={{ duration: 0.2, ease: "easeOut" }}
                        className="w-full h-full"
                    >
                        <img
                            src={`${API_BASE_URL}${currentVariant.images[currentIndex]}`}
                            alt={`Slide ${currentIndex + 1}`}
                            className="w-full h-full object-cover"
                        />
                    </motion.div>
                </AnimatePresence>

                {/* Navigation Controls */}
                <div className="absolute inset-x-0 top-1/2 -translate-y-1/2 flex justify-between px-4 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button
                        onClick={prevSlide}
                        className="p-2 bg-black/60 border border-white/10 rounded-full text-white hover:bg-cyber-cyan hover:text-black transition-all"
                    >
                        <ChevronLeft className="w-6 h-6" />
                    </button>
                    <button
                        onClick={nextSlide}
                        className="p-2 bg-black/60 border border-white/10 rounded-full text-white hover:bg-cyber-cyan hover:text-black transition-all"
                    >
                        <ChevronRight className="w-6 h-6" />
                    </button>
                </div>

                {/* Pagination Dots */}
                <div className="absolute bottom-4 inset-x-0 flex justify-center gap-1.5 ">
                    {currentVariant.images.map((_, i) => (
                        <div
                            key={i}
                            onClick={() => setCurrentIndex(i)}
                            className={cn(
                                "h-1.5 rounded-full transition-all duration-200 cursor-pointer",
                                i === currentIndex ? "w-6 bg-cyber-cyan" : "w-1.5 bg-white/30 hover:bg-white/50"
                            )}
                        />
                    ))}
                </div>

                <div className="absolute top-4 left-4 px-2 py-1 bg-black/60 backdrop-blur-md rounded border border-white/10 text-[10px] font-mono text-white/60">
                    SLIDE {currentIndex + 1} / {currentVariant.images.length}
                </div>
            </GlassCard>

            <p className="text-center text-white/40 text-[10px] uppercase tracking-widest font-mono">
                {isMultiVariant ? "3 style variants generated • Click tabs to switch" : "Generated via Playwright Neural Renderer"}
            </p>
        </div>
    );
};

export function ContentDisplay({ content, activeSection }: ContentDisplayProps) {
    const [copied, setCopied] = useState(false);
    const [selectedHook, setSelectedHook] = useState(0);

    const copyToClipboard = (text: string) => {
        navigator.clipboard.writeText(text);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    const getSEOBadgeColor = (grade: string) => {
        switch (grade) {
            case 'A': return 'bg-cyber-green text-cyber-black';
            case 'B': return 'bg-cyber-yellow text-cyber-black';
            case 'C': return 'bg-orange-500 text-white';
            default: return 'bg-red-500 text-white';
        }
    };

    return (
        <div className="w-full max-w-5xl mx-auto h-full overflow-y-auto custom-scrollbar pr-4">
            <AnimatePresence mode="wait">
                <motion.div
                    key={activeSection}
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: -20 }}
                    transition={{ duration: 0.3 }}
                    className="pb-20"
                >
                    {activeSection === "analysis" && (
                        <GlassCard variant="cyan" className="min-h-[400px]">
                            <div className="space-y-8">
                                <section>
                                    <h3 className="text-cyber-cyan font-bold uppercase tracking-widest text-sm mb-2 flex items-center gap-2">
                                        <BarChart3 className="w-4 h-4" /> The Big Idea
                                    </h3>
                                    <p className="text-xl font-medium text-white/90 italic">
                                        {content.analysis?.big_idea ? `"${content.analysis.big_idea}"` : <span className="animate-pulse">Analyzing transcript...</span>}
                                    </p>
                                </section>

                                <section>
                                    <h3 className="text-cyber-magenta font-bold uppercase tracking-widest text-sm mb-4 flex items-center gap-2">
                                        <Zap className="w-4 h-4" /> Strong Takes
                                    </h3>
                                    <div className="space-y-4">
                                        {content.analysis?.strong_takes ? (
                                            content.analysis.strong_takes.map((take, i) => (
                                                <div key={i} className="flex gap-4 items-start">
                                                    <span className="text-cyber-magenta font-mono font-bold">0{i + 1}</span>
                                                    <div className="flex-1">
                                                        <p className="text-white/80">{take}</p>
                                                        {content.broll_images?.[i] && (
                                                            <div className="mt-3 relative group">
                                                                <img
                                                                    src={content.broll_images[i].image_url}
                                                                    alt={content.broll_images[i].keyword}
                                                                    className="w-full max-w-md rounded-lg border border-white/10"
                                                                />
                                                                <div className="absolute bottom-2 left-2 px-2 py-1 bg-black/60 text-white/60 text-[10px] rounded">
                                                                    📷 {content.broll_images[i].photographer} (Pexels)
                                                                </div>
                                                            </div>
                                                        )}
                                                    </div>
                                                </div>
                                            ))
                                        ) : (
                                            <div className="text-white/40 animate-pulse">Extracting key insights...</div>
                                        )}
                                    </div>
                                </section>

                                <section>
                                    <h3 className="text-cyber-yellow font-bold uppercase tracking-widest text-sm mb-2 flex items-center gap-2">
                                        <CheckCircle2 className="w-4 h-4" /> Detected Tone
                                    </h3>
                                    <span className="px-3 py-1 bg-cyber-yellow/10 border border-cyber-yellow/30 text-cyber-yellow rounded text-xs uppercase font-bold tracking-widest">
                                        {content.analysis?.tone || "Detecting..."}
                                    </span>
                                </section>
                            </div>
                        </GlassCard>
                    )}

                    {activeSection === "linkedin" && (
                        <GlassCard variant="cyan" className="min-h-[400px]">
                            <div className="space-y-4">
                                <div className="flex justify-between items-center">
                                    <h3 className="text-cyber-blue font-bold uppercase tracking-widest text-sm flex items-center gap-2">
                                        <Linkedin className="w-4 h-4" /> LinkedIn Post (Bro-etry)
                                    </h3>
                                    <button
                                        onClick={() => content.linkedin_post && copyToClipboard(content.linkedin_post)}
                                        className="text-white/40 hover:text-cyber-cyan transition-colors"
                                        disabled={!content.linkedin_post}
                                    >
                                        {copied ? <CheckCircle2 className="w-5 h-5 text-cyber-green" /> : <Copy className="w-5 h-5" />}
                                    </button>
                                </div>
                                <div className="bg-black/40 p-6 rounded-lg border border-white/5 font-serif text-lg leading-relaxed whitespace-pre-wrap text-white/90 min-h-[300px]">
                                    {content.linkedin_post || <span className="text-white/30 animate-pulse">Generating LinkedIn post...</span>}
                                </div>
                            </div>
                        </GlassCard>
                    )}

                    {activeSection === "hooks" && (
                        <GlassCard variant="cyan" className="min-h-[400px]">
                            <div className="space-y-6">
                                <div className="flex justify-between items-center">
                                    <h3 className="text-cyber-yellow font-bold uppercase tracking-widest text-sm flex items-center gap-2">
                                        <Zap className="w-4 h-4" /> A/B Hook Variants
                                    </h3>
                                </div>

                                {content.linkedin_hooks && content.linkedin_hooks.length > 0 ? (
                                    <div className="space-y-4">
                                        {content.linkedin_hooks.map((hook, i) => (
                                            <div
                                                key={i}
                                                onClick={() => setSelectedHook(i)}
                                                className={cn(
                                                    "p-4 rounded-lg border cursor-pointer transition-all",
                                                    selectedHook === i
                                                        ? "bg-cyber-yellow/10 border-cyber-yellow"
                                                        : "bg-black/40 border-white/10 hover:border-white/30"
                                                )}
                                            >
                                                <div className="flex justify-between items-start mb-2">
                                                    <span className={cn(
                                                        "px-2 py-1 text-[10px] font-bold uppercase rounded",
                                                        selectedHook === i ? "bg-cyber-yellow text-cyber-black" : "bg-white/10 text-white/60"
                                                    )}>
                                                        {hook.framework}
                                                    </span>
                                                    <button
                                                        onClick={(e) => {
                                                            e.stopPropagation();
                                                            copyToClipboard(hook.hook);
                                                        }}
                                                        className="text-white/40 hover:text-cyber-cyan"
                                                    >
                                                        <Copy className="w-4 h-4" />
                                                    </button>
                                                </div>
                                                <p className="text-white/90 whitespace-pre-wrap">{hook.hook}</p>
                                            </div>
                                        ))}
                                    </div>
                                ) : (
                                    <div className="py-20 text-center text-white/20 font-mono uppercase tracking-widest animate-pulse">
                                        // GENERATING HOOKS...
                                    </div>
                                )}
                            </div>
                        </GlassCard>
                    )}

                    {activeSection === "twitter" && (
                        <GlassCard variant="cyan" className="min-h-[400px]">
                            <div className="space-y-6">
                                <div className="flex justify-between items-center">
                                    <h3 className="text-cyber-cyan font-bold uppercase tracking-widest text-sm flex items-center gap-2">
                                        <Twitter className="w-4 h-4" /> Twitter Thread
                                    </h3>
                                    <button
                                        onClick={() => content.twitter_thread && copyToClipboard(content.twitter_thread.join("\n\n---\n\n"))}
                                        className="text-white/40 hover:text-cyber-cyan transition-colors"
                                        disabled={!content.twitter_thread}
                                    >
                                        {copied ? <CheckCircle2 className="w-5 h-5 text-cyber-green" /> : <Copy className="w-5 h-5" />}
                                    </button>
                                </div>
                                <div className="space-y-4 min-h-[300px]">
                                    {content.twitter_thread && content.twitter_thread.length > 0 ? (
                                        content.twitter_thread.map((tweet, i) => (
                                            <div key={i} className="bg-black/40 p-4 rounded-lg border border-cyber-cyan/10 relative">
                                                <span className="absolute -top-2 -left-2 w-6 h-6 bg-cyber-cyan text-cyber-black text-[10px] font-bold flex items-center justify-center rounded-full">
                                                    {i + 1}
                                                </span>
                                                <p className="text-white/80 whitespace-pre-wrap">{tweet}</p>
                                            </div>
                                        ))
                                    ) : (
                                        <div className="text-white/30 animate-pulse">Generating thread...</div>
                                    )}
                                </div>
                            </div>
                        </GlassCard>
                    )}

                    {activeSection === "blog" && (
                        <GlassCard variant="magenta" className="min-h-[400px]">
                            <div className="space-y-4">
                                <div className="flex justify-between items-center">
                                    <div className="flex items-center gap-4">
                                        <h3 className="text-cyber-magenta font-bold uppercase tracking-widest text-sm flex items-center gap-2">
                                            <FileText className="w-4 h-4" /> SEO Blog Post
                                        </h3>
                                        {content.seo_score && (
                                            <span className={cn(
                                                "px-3 py-1 text-xs font-bold rounded flex items-center gap-1",
                                                getSEOBadgeColor(content.seo_score.grade)
                                            )}>
                                                <Award className="w-3 h-3" />
                                                SEO: {content.seo_score.grade} ({content.seo_score.score}/{content.seo_score.max_score})
                                            </span>
                                        )}
                                    </div>
                                    <button
                                        onClick={() => content.blog_post && copyToClipboard(content.blog_post)}
                                        className="text-white/40 hover:text-cyber-magenta transition-colors"
                                        disabled={!content.blog_post}
                                    >
                                        {copied ? <CheckCircle2 className="w-5 h-5 text-cyber-green" /> : <Copy className="w-5 h-5" />}
                                    </button>
                                </div>

                                {content.seo_score?.feedback && content.seo_score.feedback.length > 0 && (
                                    <div className="bg-black/30 p-4 rounded border border-white/10 text-sm">
                                        <p className="text-white/60 mb-2 text-xs uppercase font-bold">SEO Feedback:</p>
                                        <ul className="space-y-1">
                                            {content.seo_score.feedback.map((item, i) => (
                                                <li key={i} className="text-white/60">{item}</li>
                                            ))}
                                        </ul>
                                    </div>
                                )}

                                <div className="prose prose-invert max-w-none bg-black/40 p-8 rounded-lg border border-cyber-magenta/10 min-h-[300px]">
                                    {content.blog_post ? (
                                        <ReactMarkdown>{content.blog_post}</ReactMarkdown>
                                    ) : (
                                        <div className="text-white/30 animate-pulse">Writing blog post (this takes a moment)...</div>
                                    )}
                                </div>
                            </div>
                        </GlassCard>
                    )}

                    {activeSection === "newsletter" && (
                        <GlassCard variant="cyan" className="min-h-[400px]">
                            <div className="space-y-4">
                                <div className="flex justify-between items-center">
                                    <h3 className="text-cyber-yellow font-bold uppercase tracking-widest text-sm flex items-center gap-2">
                                        <Mail className="w-4 h-4" /> HTML Newsletter
                                    </h3>
                                    <div className="flex gap-2">
                                        <button
                                            onClick={() => content.newsletter_html && copyToClipboard(content.newsletter_html)}
                                            className="text-white/40 hover:text-cyber-cyan transition-colors"
                                            disabled={!content.newsletter_html}
                                        >
                                            {copied ? <CheckCircle2 className="w-5 h-5 text-cyber-green" /> : <Copy className="w-5 h-5" />}
                                        </button>
                                    </div>
                                </div>

                                <div className="bg-white rounded-lg overflow-hidden min-h-[500px] border border-white/10">
                                    {content.newsletter_html ? (
                                        <iframe
                                            srcDoc={content.newsletter_html}
                                            className="w-full h-[600px] bg-white border-none"
                                            title="Newsletter Preview"
                                        />
                                    ) : (
                                        <div className="w-full h-full bg-black/40 flex flex-col items-center justify-center gap-4 min-h-[400px]">
                                            <Mail className="w-10 h-10 text-white/20 animate-pulse" />
                                            <div className="text-white/30 animate-pulse font-mono uppercase tracking-widest text-xs">
                                                Designing HTML Email...
                                            </div>
                                        </div>
                                    )}
                                </div>
                            </div>
                        </GlassCard>
                    )}

                    {activeSection === "research" && (
                        <GlassCard variant="cyan" className="min-h-[400px]">
                            <div className="space-y-8">
                                <section>
                                    <h3 className="text-cyber-purple font-bold uppercase tracking-widest text-sm mb-4 flex items-center gap-2">
                                        <TrendingUp className="w-4 h-4" /> Trend-Jacking Context
                                    </h3>
                                    <div className="bg-cyber-purple/5 border border-cyber-purple/20 p-5 rounded-xl">
                                        {content.research?.trend_context ? (
                                            <p className="text-white/90 leading-relaxed italic">
                                                "{content.research.trend_context}"
                                            </p>
                                        ) : (
                                            <div className="text-white/20 animate-pulse font-mono flex items-center gap-3">
                                                <RefreshCcw className="w-4 h-4 animate-spin" /> BROWSING FOR TRENDS...
                                            </div>
                                        )}
                                    </div>
                                </section>

                                <section>
                                    <h3 className="text-cyber-green font-bold uppercase tracking-widest text-sm mb-4 flex items-center gap-2">
                                        <ShieldCheck className="w-4 h-4" /> Neural Fact-Checker
                                    </h3>
                                    <div className="space-y-4">
                                        {content.research?.fact_checks && content.research.fact_checks.length > 0 ? (
                                            content.research.fact_checks.map((check, i) => (
                                                <div key={i} className="bg-black/40 border border-white/5 p-4 rounded-lg">
                                                    <div className="flex justify-between items-start mb-2">
                                                        <span className="text-xs font-mono text-white/40 uppercase">Claim: {check.claim}</span>
                                                        <span className={cn(
                                                            "px-2 py-0.5 rounded text-[10px] font-bold uppercase",
                                                            check.verdict === "Correct" ? "bg-green-500/20 text-green-400" :
                                                                check.verdict === "Misleading" ? "bg-yellow-500/20 text-yellow-400" : "bg-red-500/20 text-red-400"
                                                        )}>
                                                            {check.verdict}
                                                        </span>
                                                    </div>
                                                    <p className="text-sm text-white/80">{check.explanation}</p>
                                                </div>
                                            ))
                                        ) : (
                                            <div className="text-white/20 animate-pulse font-mono">// VERIFYING CLAIMS...</div>
                                        )}
                                    </div>
                                </section>
                            </div>
                        </GlassCard>
                    )}

                    {activeSection === "carousel" && (
                        <CarouselPreview
                            carousel={content.carousel}
                        />
                    )}

                    {activeSection === "thumbnails" && (
                        <GlassCard variant="cyan" className="min-h-[400px]">
                            <div className="space-y-6">
                                <h3 className="text-cyber-cyan font-bold uppercase tracking-widest text-sm flex items-center gap-2">
                                    <ImageIcon className="w-4 h-4" /> High-CTR Thumbnail A/B Variants
                                </h3>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                    {content.thumbnails ? (
                                        content.thumbnails.map((thumb, i) => (
                                            <div key={i} className="group relative rounded-xl overflow-hidden border border-white/10 aspect-video bg-black/40">
                                                <img
                                                    src={`${API_BASE_URL}${thumb}`}
                                                    alt={`Thumbnail variant ${i + 1}`}
                                                    className="w-full h-full object-cover transition-transform group-hover:scale-105 duration-700"
                                                />
                                                <div className="absolute top-2 left-2 px-2 py-0.5 bg-black/60 text-cyber-cyan text-[10px] font-bold uppercase rounded border border-cyber-cyan/30">
                                                    Variant {i + 1}
                                                </div>
                                                <div className="absolute inset-0 bg-black/0 group-hover:bg-black/40 transition-all flex items-center justify-center opacity-0 group-hover:opacity-100">
                                                    <a
                                                        href={`${API_BASE_URL}${thumb}`}
                                                        download
                                                        className="p-3 bg-cyber-cyan text-cyber-black rounded-full shadow-lg"
                                                    >
                                                        <Download className="w-5 h-5" />
                                                    </a>
                                                </div>
                                            </div>
                                        ))
                                    ) : (
                                        [1, 2, 3].map((_, i) => (
                                            <div key={i} className="rounded-xl border border-white/5 aspect-video bg-white/5 animate-pulse flex items-center justify-center">
                                                <ImageIcon className="w-8 h-8 text-white/10" />
                                            </div>
                                        ))
                                    )}
                                </div>
                            </div>
                        </GlassCard>
                    )}

                    {activeSection === "audio" && (
                        <GlassCard variant="cyan" className="min-h-[400px] flex items-center justify-center">
                            <div className="text-center space-y-6 p-10">
                                <div className="relative inline-block">
                                    <div className="absolute -inset-4 bg-cyber-cyan/20 blur-xl rounded-full animate-pulse"></div>
                                    <div className="relative w-24 h-24 rounded-full bg-gradient-to-br from-cyber-cyan to-cyber-blue flex items-center justify-center shadow-lg border border-white/20">
                                        <Volume2 className="w-10 h-10 text-cyber-black" />
                                    </div>
                                </div>

                                <div className="space-y-2">
                                    <h2 className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-white/60">
                                        Neural Dubbing: {content.audio?.lang || "Detecting..."}
                                    </h2>
                                    <p className="text-white/40 font-mono text-xs uppercase tracking-[0.2em]">
                                        Voice Cloning & Translation
                                    </p>
                                </div>

                                {content.audio?.error ? (
                                    <div className="p-4 bg-red-500/20 border border-red-500/50 rounded-lg text-red-200 text-sm font-mono uppercase">
                                        Neural Dubbing Failed: {content.audio.error}
                                    </div>
                                ) : content.audio?.path ? (
                                    <div className="space-y-4">
                                        <audio controls className="w-full max-w-md mx-auto custom-audio-player">
                                            <source src={`${API_BASE_URL}${content.audio.path}`} type="audio/mpeg" />
                                            Your browser does not support the audio element.
                                        </audio>
                                        <div className="flex justify-center gap-4">
                                            <a
                                                href={`${API_BASE_URL}${content.audio.path}`}
                                                download
                                                className="px-6 py-2 bg-white/10 border border-white/10 text-white font-bold uppercase text-xs rounded-lg hover:bg-white/20 transition-all flex items-center gap-2"
                                            >
                                                <Download className="w-4 h-4" /> Download Audio
                                            </a>
                                        </div>
                                    </div>
                                ) : (
                                    <div className="space-y-3">
                                        <div className="flex gap-1 justify-center">
                                            {[1, 2, 3, 4, 5].map((i) => (
                                                <motion.div
                                                    key={i}
                                                    animate={{ height: [10, 30, 10] }}
                                                    transition={{ duration: 0.8, repeat: Infinity, delay: i * 0.1 }}
                                                    className="w-1 bg-cyber-cyan rounded-full"
                                                />
                                            ))}
                                        </div>
                                        <p className="text-cyber-cyan font-mono text-[10px] uppercase animate-pulse">
                                            Cloning Timbre & Translating...
                                        </p>
                                    </div>
                                )}
                            </div>
                        </GlassCard>
                    )}
                </motion.div>
            </AnimatePresence>
        </div>
    );
}
