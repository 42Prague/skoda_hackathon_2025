"use client";

import { useState, useEffect, useMemo } from "react";
import courses from "@/data/courses.json";
import { Clock, ArrowRight, Layers, Play, X, CheckCircle, Loader2, BookOpen, ExternalLink, Search } from "lucide-react";
import { toast } from "sonner";

type Course = typeof courses[number];

export default function FeedPage() {
    const [activeTab, setActiveTab] = useState<"all" | "professional" | "digital" | "leadership">("all");
    const [searchTerm, setSearchTerm] = useState("");
    const [startedModules, setStartedModules] = useState<Set<string>>(new Set());
    const [completedModules, setCompletedModules] = useState<Set<string>>(new Set());
    const [activeModule, setActiveModule] = useState<Course | null>(null);

    // Load started modules from localStorage
    useEffect(() => {
        if (typeof window !== "undefined") {
            const stored = localStorage.getItem("started_modules");
            if (stored) {
                try {
                    const parsed = JSON.parse(stored);
                    setStartedModules(new Set(parsed));
                } catch (e) {
                    // If parsing fails, start with empty set
                }
            }
        }
    }, []);

    // Load completed modules from localStorage
    useEffect(() => {
        if (typeof window !== "undefined") {
            const stored = localStorage.getItem("completed_modules");
            if (stored) {
                try {
                    const parsed = JSON.parse(stored);
                    setCompletedModules(new Set(parsed));
                } catch (e) {
                    // If parsing fails, start with empty set
                }
            }
        }
    }, []);

    // Save started modules to localStorage
    useEffect(() => {
        if (typeof window !== "undefined" && startedModules.size > 0) {
            localStorage.setItem("started_modules", JSON.stringify(Array.from(startedModules)));
        }
    }, [startedModules]);

    // Save completed modules to localStorage
    useEffect(() => {
        if (typeof window !== "undefined" && completedModules.size > 0) {
            localStorage.setItem("completed_modules", JSON.stringify(Array.from(completedModules)));
        }
    }, [completedModules]);

    const handleStartModule = (course: Course) => {
        // If already completed, don't do anything
        if (completedModules.has(course.title)) {
            setActiveModule(course);
            return;
        }

        // If not started yet, mark as started and open modal
        if (!startedModules.has(course.title)) {
            setStartedModules((prev) => {
                const newSet = new Set(prev);
                newSet.add(course.title);
                return newSet;
            });
            toast.success("Module Started", {
                description: `"${course.title}" is now in progress.`,
                duration: 3000,
            });
        }

        // Open the modal
        setActiveModule(course);
    };

    const handleCompleteModule = (course: Course) => {
        setCompletedModules((prev) => {
            const newSet = new Set(prev);
            newSet.add(course.title);
            return newSet;
        });
        // Remove from started if it was there
        setStartedModules((prev) => {
            const newSet = new Set(prev);
            newSet.delete(course.title);
            return newSet;
        });
        toast.success("Module Completed!", {
            description: `Congratulations! You've completed "${course.title}".`,
            duration: 3000,
        });
        setActiveModule(null);
    };

    const categorySummary: Record<string, number> = {};
    courses.forEach((course: Course) => {
        const key = course.category || "Professional Skills";
        categorySummary[key] = (categorySummary[key] || 0) + 1;
    });

    const filteredCourses = useMemo(() => {
        let filtered = courses;

        // Filter by tab
        if (activeTab !== "all") {
            const categoryMap: Record<string, string> = {
                professional: "Professional Skills",
                digital: "Digital & Data",
                leadership: "Leadership & Management",
            };
            filtered = filtered.filter(course => course.category === categoryMap[activeTab]);
        }

        // Filter by search term
        if (searchTerm) {
            const searchLower = searchTerm.toLowerCase();
            filtered = filtered.filter(course =>
                course.title.toLowerCase().includes(searchLower) ||
                course.topic?.toLowerCase().includes(searchLower) ||
                course.source?.toLowerCase().includes(searchLower) ||
                (course as any).description?.toLowerCase().includes(searchLower) ||
                course.category?.toLowerCase().includes(searchLower)
            );
        }

        return filtered;
    }, [activeTab, searchTerm]);

    const tabs = [
        { id: "all" as const, label: "All Courses", count: courses.length },
        { id: "professional" as const, label: "Professional Skills", count: categorySummary["Professional Skills"] || 0 },
        { id: "digital" as const, label: "Digital & Data", count: categorySummary["Digital & Data"] || 0 },
        { id: "leadership" as const, label: "Leadership", count: categorySummary["Leadership & Management"] || 0 },
    ];

    const [streak, setStreak] = useState(0);

    // Load streak from localStorage
    useEffect(() => {
        if (typeof window !== "undefined") {
            const storedStreak = parseInt(localStorage.getItem("learning_streak") || "0");
            const lastVisit = localStorage.getItem("last_visit_date");
            const today = new Date().toISOString().split('T')[0];

            if (lastVisit === today) {
                setStreak(storedStreak);
            } else if (lastVisit) {
                const lastDate = new Date(lastVisit);
                const currentDate = new Date(today);
                const diffTime = Math.abs(currentDate.getTime() - lastDate.getTime());
                const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

                if (diffDays === 1) {
                    const newStreak = storedStreak + 1;
                    setStreak(newStreak);
                    localStorage.setItem("learning_streak", newStreak.toString());
                    toast.success("Streak Increased!", {
                        description: `You're on a ${newStreak}-day learning streak! 🔥`,
                        duration: 3000,
                    });
                } else {
                    setStreak(1);
                    localStorage.setItem("learning_streak", "1");
                }
            } else {
                setStreak(1);
                localStorage.setItem("learning_streak", "1");
            }
            localStorage.setItem("last_visit_date", today);
        }
    }, []);

    // ... existing code ...

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between flex-wrap gap-4">
                <div>
                    <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">Your Learning Feed</h1>
                    <p className="text-slate-500 dark:text-slate-400">Micro-modules across Škoda Academy tracks.</p>
                </div>
                <div className="flex gap-2 items-center">
                    {/* Streak Counter */}
                    <div className="flex items-center gap-1.5 px-3 py-1.5 bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-400 rounded-full text-sm font-bold border border-orange-200 dark:border-orange-800/50" title="Daily Learning Streak">
                        <span className="text-lg">🔥</span>
                        <span>{streak}</span>
                    </div>

                    <div className="relative">
                        <Search className="absolute left-3 top-3 text-slate-400" size={18} />
                        <input
                            type="text"
                            placeholder="Search courses..."
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            className="pl-10 pr-4 py-2 border border-slate-300 dark:border-slate-700 rounded-lg bg-slate-50 dark:bg-slate-900 text-slate-900 dark:text-slate-100 focus:ring-2 focus:ring-emerald-500 focus:border-transparent outline-none transition-all"
                        />
                    </div>
                    <span className="px-3 py-1 bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-400 rounded-full text-xs font-medium border border-emerald-200 dark:border-emerald-800/50">
                        {filteredCourses.length} Modules
                    </span>
                </div>
            </div>

            {/* Tabs */}
            <div className="flex gap-2 border-b border-slate-200 dark:border-slate-800 overflow-x-auto">
                {tabs.map((tab) => (
                    <button
                        key={tab.id}
                        onClick={() => setActiveTab(tab.id)}
                        className={`px-4 py-2 font-medium transition-colors border-b-2 whitespace-nowrap ${activeTab === tab.id
                                ? "border-emerald-500 text-emerald-600 dark:text-emerald-400"
                                : "border-transparent text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-300"
                            }`}
                    >
                        {tab.label}
                        <span className="ml-2 px-2 py-0.5 bg-slate-100 dark:bg-slate-800 rounded-full text-xs">
                            {tab.count}
                        </span>
                    </button>
                ))}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                {Object.entries(categorySummary)
                    .sort((a, b) => b[1] - a[1])
                    .slice(0, 3)
                    .map(([category, count]) => (
                        <div key={category} className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 flex items-center gap-3">
                            <div className="p-3 rounded-lg bg-emerald-50 dark:bg-emerald-900/30 text-emerald-600">
                                <Layers size={20} />
                            </div>
                            <div>
                                <p className="text-sm text-slate-500">{category}</p>
                                <p className="text-lg font-semibold text-slate-900 dark:text-slate-100">{count} modules</p>
                            </div>
                        </div>
                    ))}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {filteredCourses.map((course: Course, index: number) => (
                    <div
                        key={index}
                        className="group bg-white dark:bg-slate-950 rounded-xl border border-slate-200 dark:border-slate-800 p-5 hover:shadow-md transition-all hover:border-emerald-500/50"
                    >
                        <div className="flex items-start justify-between mb-4">
                            <div className="flex gap-2">
                                <span className="px-2 py-1 rounded-md text-[10px] font-bold uppercase tracking-wider bg-slate-100 text-slate-700">
                                    {course.category || "Skills"}
                                </span>
                                {course.provider && (
                                    <span className="px-2 py-1 bg-slate-50 dark:bg-slate-900 text-slate-500 rounded-md text-[10px] font-medium uppercase tracking-wider">
                                        {course.provider}
                                    </span>
                                )}
                            </div>
                        </div>

                        <h3 className="font-semibold text-slate-900 dark:text-slate-100 mb-2 line-clamp-2 group-hover:text-emerald-600 transition-colors">
                            {course.title}
                        </h3>

                        <p className="text-sm text-slate-500 dark:text-slate-400 mb-4 line-clamp-3">
                            {course.topic || course.source}
                        </p>

                        <div className="flex items-center justify-between mt-auto pt-4 border-t border-slate-100 dark:border-slate-900">
                            <div className="flex items-center gap-1 text-xs text-slate-400">
                                <Clock size={14} />
                                <span>{course.content_type || "Micro-learning"}</span>
                            </div>
                            <button
                                onClick={() => handleStartModule(course)}
                                className={`text-sm font-medium flex items-center gap-1 hover:gap-2 transition-all ${completedModules.has(course.title)
                                        ? "text-emerald-600 dark:text-emerald-400"
                                        : startedModules.has(course.title)
                                            ? "text-amber-600 dark:text-amber-400"
                                            : "text-emerald-600 hover:text-emerald-700 dark:text-emerald-400 dark:hover:text-emerald-300"
                                    }`}
                            >
                                {completedModules.has(course.title) ? (
                                    <>
                                        <CheckCircle size={16} /> Completed
                                    </>
                                ) : startedModules.has(course.title) ? (
                                    <>
                                        <Loader2 size={16} className="animate-spin" /> Continue
                                    </>
                                ) : (
                                    <>
                                        Start <ArrowRight size={16} />
                                    </>
                                )}
                            </button>
                        </div>
                    </div>
                ))}
            </div>

            {/* Course Modal */}
            {activeModule && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
                    <div className="bg-white dark:bg-slate-950 rounded-2xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col">
                        <div className="p-6 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
                            <div>
                                <h2 className="text-2xl font-bold text-slate-900 dark:text-slate-100">
                                    {activeModule.title}
                                </h2>
                                <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
                                    {activeModule.category} • {activeModule.content_type || "Micro-learning"}
                                </p>
                            </div>
                            <button
                                onClick={() => setActiveModule(null)}
                                className="p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors"
                            >
                                <X size={24} className="text-slate-500" />
                            </button>
                        </div>
                        <div className="flex-1 overflow-y-auto p-6">
                            <div className="space-y-6">
                                {/* Demo Notice */}
                                <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
                                    <div className="flex items-start gap-3">
                                        <div className="text-blue-600 dark:text-blue-400 mt-0.5">
                                            <BookOpen size={20} />
                                        </div>
                                        <div>
                                            <h4 className="text-sm font-semibold text-blue-900 dark:text-blue-100 mb-1">
                                                Demo Mode
                                            </h4>
                                            <p className="text-sm text-blue-800 dark:text-blue-200">
                                                This is a prototype demonstration. In production, clicking "Start" would open the actual course content (PDF, video, or interactive module) from Škoda's Learning Management System.
                                            </p>
                                        </div>
                                    </div>
                                </div>

                                {/* Course Overview */}
                                <div>
                                    <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-2">
                                        About this Module
                                    </h3>
                                    <p className="text-slate-600 dark:text-slate-400">
                                        {(activeModule as any).description || activeModule.topic || activeModule.source || "This micro-module is designed to help you develop essential skills for your role."}
                                    </p>
                                    {(activeModule as any).job_description && (
                                        <div className="mt-3 p-3 bg-slate-50 dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-800">
                                            <p className="text-xs font-medium text-slate-500 dark:text-slate-400 mb-1">Job Context</p>
                                            <p className="text-sm text-slate-600 dark:text-slate-400">{(activeModule as any).job_description}</p>
                                        </div>
                                    )}
                                    {activeModule.provider && (
                                        <p className="text-sm text-slate-500 dark:text-slate-400 mt-2">
                                            Provider: {activeModule.provider}
                                        </p>
                                    )}
                                    <p className="text-sm text-slate-500 dark:text-slate-400 mt-2">
                                        Source: {activeModule.source || "Škoda Academy"}
                                    </p>
                                </div>

                                {/* Course Content Sections */}
                                <div className="space-y-4">
                                    <h4 className="text-md font-semibold text-slate-900 dark:text-slate-100">
                                        Course Content
                                    </h4>

                                    {/* Section 1: Introduction */}
                                    <div className="bg-slate-50 dark:bg-slate-900 rounded-lg p-4 border border-slate-200 dark:border-slate-800">
                                        <div className="flex items-center gap-3 mb-3">
                                            <div className="w-8 h-8 rounded-full bg-emerald-100 dark:bg-emerald-900 flex items-center justify-center text-emerald-600 dark:text-emerald-400 font-semibold">
                                                1
                                            </div>
                                            <h5 className="font-semibold text-slate-900 dark:text-slate-100">Introduction</h5>
                                            <CheckCircle size={16} className="text-emerald-500 ml-auto" />
                                        </div>
                                        <p className="text-sm text-slate-600 dark:text-slate-400 ml-11">
                                            Welcome to this micro-learning module. In this {activeModule.title.includes("QMS") ? "Quality Management System" : activeModule.title.includes("CONTROLLING") ? "Controlling" : "course"}, you'll learn the fundamentals and key concepts.
                                        </p>
                                    </div>

                                    {/* Section 2: Core Concepts */}
                                    <div className="bg-slate-50 dark:bg-slate-900 rounded-lg p-4 border border-slate-200 dark:border-slate-800">
                                        <div className="flex items-center gap-3 mb-3">
                                            <div className="w-8 h-8 rounded-full bg-emerald-100 dark:bg-emerald-900 flex items-center justify-center text-emerald-600 dark:text-emerald-400 font-semibold">
                                                2
                                            </div>
                                            <h5 className="font-semibold text-slate-900 dark:text-slate-100">Core Concepts</h5>
                                            <CheckCircle size={16} className="text-emerald-500 ml-auto" />
                                        </div>
                                        <div className="ml-11 space-y-2 text-sm text-slate-600 dark:text-slate-400">
                                            {activeModule.title.includes("QMS") ? (
                                                <>
                                                    <p>• Understanding quality management principles and standards</p>
                                                    <p>• Key components of a Quality Management System</p>
                                                    <p>• Implementation best practices and compliance requirements</p>
                                                </>
                                            ) : activeModule.title.includes("CONTROLLING") ? (
                                                <>
                                                    <p>• What is Controlling and its role in business management</p>
                                                    <p>• Key controlling processes and methodologies</p>
                                                    <p>• Financial and operational controlling techniques</p>
                                                </>
                                            ) : (
                                                <>
                                                    <p>• Key principles and foundational knowledge</p>
                                                    <p>• Best practices and industry standards</p>
                                                    <p>• Practical applications in your role</p>
                                                </>
                                            )}
                                        </div>
                                    </div>

                                    {/* Section 3: Practical Application */}
                                    <div className="bg-slate-50 dark:bg-slate-900 rounded-lg p-4 border border-slate-200 dark:border-slate-800">
                                        <div className="flex items-center gap-3 mb-3">
                                            <div className="w-8 h-8 rounded-full bg-amber-100 dark:bg-amber-900 flex items-center justify-center text-amber-600 dark:text-amber-400 font-semibold">
                                                3
                                            </div>
                                            <h5 className="font-semibold text-slate-900 dark:text-slate-100">Practical Application</h5>
                                            <Loader2 size={16} className="text-amber-500 ml-auto animate-spin" />
                                        </div>
                                        <p className="text-sm text-slate-600 dark:text-slate-400 ml-11">
                                            Apply what you've learned through interactive scenarios and real-world examples relevant to your role at Škoda.
                                        </p>
                                    </div>

                                    {/* Section 4: Assessment */}
                                    <div className="bg-slate-50 dark:bg-slate-900 rounded-lg p-4 border border-slate-200 dark:border-slate-800 opacity-60">
                                        <div className="flex items-center gap-3 mb-3">
                                            <div className="w-8 h-8 rounded-full bg-slate-200 dark:bg-slate-700 flex items-center justify-center text-slate-500 dark:text-slate-400 font-semibold">
                                                4
                                            </div>
                                            <h5 className="font-semibold text-slate-500 dark:text-slate-400">Quick Assessment</h5>
                                        </div>
                                        <p className="text-sm text-slate-500 dark:text-slate-400 ml-11">
                                            Complete a short quiz to verify your understanding (available after completing previous sections).
                                        </p>
                                    </div>
                                </div>

                                {/* Progress Indicator */}
                                <div className="bg-emerald-50 dark:bg-emerald-900/20 border border-emerald-200 dark:border-emerald-800 rounded-lg p-4">
                                    <div className="flex items-center justify-between mb-2">
                                        <span className="text-sm font-medium text-emerald-900 dark:text-emerald-100">Progress</span>
                                        <span className="text-sm font-semibold text-emerald-700 dark:text-emerald-300">50%</span>
                                    </div>
                                    <div className="w-full bg-emerald-200 dark:bg-emerald-800 rounded-full h-2">
                                        <div className="bg-emerald-600 h-2 rounded-full" style={{ width: "50%" }}></div>
                                    </div>
                                    <p className="text-xs text-emerald-700 dark:text-emerald-300 mt-2">
                                        2 of 4 sections completed • Estimated time remaining: 2-3 minutes
                                    </p>
                                </div>
                            </div>
                        </div>
                        <div className="p-6 border-t border-slate-200 dark:border-slate-800 flex gap-3">
                            {!completedModules.has(activeModule.title) && (
                                <>
                                    <button
                                        onClick={() => {
                                            toast.info("Course Content", {
                                                description: "In production, this would open the actual course content (PDF, video, or interactive module) from the LMS.",
                                                duration: 4000,
                                            });
                                        }}
                                        className="flex-1 py-3 bg-slate-900 dark:bg-slate-100 text-white dark:text-slate-900 rounded-lg font-medium hover:opacity-90 transition-opacity flex items-center justify-center gap-2"
                                    >
                                        <ExternalLink size={20} /> Open Course Content
                                    </button>
                                    <button
                                        onClick={() => handleCompleteModule(activeModule)}
                                        className="flex-1 py-3 bg-emerald-600 text-white rounded-lg font-medium hover:bg-emerald-700 transition-colors flex items-center justify-center gap-2"
                                    >
                                        <CheckCircle size={20} /> Mark as Completed
                                    </button>
                                </>
                            )}
                            <button
                                onClick={() => setActiveModule(null)}
                                className={`px-6 py-3 bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 rounded-lg font-medium hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors ${completedModules.has(activeModule.title) ? "flex-1" : ""
                                    }`}
                            >
                                {completedModules.has(activeModule.title) ? "Close" : "Continue Later"}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
