"use client";

import { useParams } from "next/navigation";
import Link from "next/link";
import { useState, useEffect, useMemo } from "react";
import { ArrowLeft, CheckCircle, Play, AlertCircle, Award, BookOpen, GraduationCap, Briefcase, Check, X, Clock, Loader2, ExternalLink } from "lucide-react";
import { toast } from "sonner";
import usersData from "@/data/users.json";
import coursesData from "@/data/courses.json";

type UserProfile = typeof usersData[number];
type Course = typeof coursesData[number];

interface AssignedModule {
    courseTitle: string;
    courseId: string;
    assignedDate: string;
    status: "assigned" | "in-progress" | "completed";
}

export default function EmployeeDetailPage() {
    const params = useParams();
    const userId = params.id as string;
    const user: UserProfile | undefined = usersData.find((u) => u.id === userId);

    const [activeTab, setActiveTab] = useState<"overview" | "skills" | "learning" | "assignments">("overview");
    const [assignedModules, setAssignedModules] = useState<AssignedModule[]>([]);
    const [activeModule, setActiveModule] = useState<Course | null>(null);

    // Load assigned modules from localStorage
    useEffect(() => {
        if (typeof window !== "undefined") {
            const stored = localStorage.getItem(`assigned_modules_${userId}`);
            if (stored) {
                setAssignedModules(JSON.parse(stored));
            }
        }
    }, [userId]);

    // Save assigned modules to localStorage
    useEffect(() => {
        if (typeof window !== "undefined" && assignedModules.length >= 0) {
            localStorage.setItem(`assigned_modules_${userId}`, JSON.stringify(assignedModules));
        }
    }, [assignedModules, userId]);

    const handleAssignModule = (course: Course) => {
        const isAlreadyAssigned = assignedModules.some(
            (m) => m.courseTitle === course.title
        );

        if (isAlreadyAssigned) {
            toast.info("Module Already Assigned", {
                description: `"${course.title}" is already assigned to ${user?.name}.`,
                duration: 3000,
            });
            return;
        }

        const newAssignment: AssignedModule = {
            courseTitle: course.title,
            courseId: course.title, // Using title as ID for now
            assignedDate: new Date().toISOString(),
            status: "assigned",
        };

        setAssignedModules((prev) => [...prev, newAssignment]);
        toast.success("Module Assigned Successfully", {
            description: `"${course.title}" has been assigned to ${user?.name}.`,
            duration: 3000,
        });
    };

    const handleUnassignModule = (courseTitle: string) => {
        setAssignedModules((prev) => prev.filter((m) => m.courseTitle !== courseTitle));
        toast.success("Module Unassigned", {
            description: `"${courseTitle}" has been removed from ${user?.name}'s assignments.`,
            duration: 3000,
        });
    };

    const isModuleAssigned = (courseTitle: string) => {
        return assignedModules.some((m) => m.courseTitle === courseTitle);
    };

    const assignedModulesList = useMemo(() => {
        return assignedModules.map((assignment) => {
            const course = coursesData.find((c) => c.title === assignment.courseTitle);
            return { ...assignment, course };
        }).filter((item) => item.course) as (AssignedModule & { course: Course })[];
    }, [assignedModules]);

    if (!user) {
        return <div className="p-8 text-center">User not found</div>;
    }
    // Define expected skill levels by role
    const ROLE_EXPECTATIONS: Record<string, Record<string, string>> = {
        "Senior": { "Compliance": "advanced", "Data Storytelling": "intermediate", "Automation": "intermediate" },
        "Junior": { "Compliance": "intermediate", "Data Storytelling": "beginner", "Automation": "beginner" },
        "Manager": { "Compliance": "advanced", "Data Storytelling": "advanced", "People Operations": "advanced" },
        "Specialist": { "Compliance": "intermediate", "Data Storytelling": "intermediate", "Automation": "advanced" }
    };

    // Helper to check if level is sufficient (beginner < intermediate < advanced)
    const isGap = (current: string, expected: string) => {
        const levels = ["beginner", "intermediate", "advanced"];
        return levels.indexOf(current.toLowerCase()) < levels.indexOf(expected.toLowerCase());
    };

    // Determine role category (simplified)
    const roleCategory = user.role.includes("Senior") ? "Senior" :
        user.role.includes("Manager") ? "Manager" :
            user.role.includes("Specialist") ? "Specialist" : "Junior";

    const expectations = ROLE_EXPECTATIONS[roleCategory] || ROLE_EXPECTATIONS["Junior"];

    const skillEntries = Object.entries(user.skills || {}).map(([name, level]) => ({
        name,
        level,
        gap: expectations[name] ? isGap(level, expectations[name]) : false,
        expected: expectations[name]
    }));

    const skills = skillEntries.length ? skillEntries : [
        { name: "Data Storytelling", level: "intermediate", gap: isGap("intermediate", expectations["Data Storytelling"] || "beginner") },
        { name: "Automation", level: "beginner", gap: isGap("beginner", expectations["Automation"] || "beginner") },
        { name: "Compliance", level: "advanced", gap: isGap("advanced", expectations["Compliance"] || "intermediate") },
        { name: "People Operations", level: "advanced", gap: isGap("advanced", expectations["People Operations"] || "beginner") }
    ];

    const priorityCategories = (user.course_mix || []).map((mix: { category: string }) => mix.category);
    const recommendations = coursesData.filter((course: Course) => {
        if (!skills.some(s => s.gap)) return true;
        return priorityCategories.includes(course.category);
    }).slice(0, 6);

    return (
        <div className="space-y-8">
            {/* Header */}
            <div className="flex items-center gap-4">
                <Link href="/" className="p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-full transition-colors">
                    <ArrowLeft size={24} />
                </Link>
                <div>
                    <h1 className="text-3xl font-bold text-slate-900 dark:text-slate-100">{user.name}</h1>
                    <p className="text-slate-500">{user.department} • {user.role}</p>
                    <p className="text-sm text-slate-500">
                        {user.position} • {user.experience_years ? `${user.experience_years} yrs exp` : null}
                    </p>
                </div>
            </div>

            {/* Tabs */}
            <div className="flex gap-2 border-b border-slate-200 dark:border-slate-800">
                {[
                    { id: "overview" as const, label: "Overview", icon: "👤" },
                    { id: "skills" as const, label: "Skills", icon: "🎯" },
                    { id: "learning" as const, label: "Learning", icon: "📚" },
                    { id: "assignments" as const, label: "Assignments", icon: "📋" },
                ].map((tab) => (
                    <button
                        key={tab.id}
                        onClick={() => setActiveTab(tab.id)}
                        className={`px-6 py-3 font-medium transition-colors border-b-2 ${activeTab === tab.id
                                ? "border-emerald-500 text-emerald-600 dark:text-emerald-400"
                                : "border-transparent text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-300"
                            }`}
                    >
                        <span className="mr-2">{tab.icon}</span>
                        {tab.label}
                    </button>
                ))}
            </div>

            {/* Tab Content */}
            {activeTab === "overview" && (
                <>
                    {/* Profile Snapshot */}
                    <section className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        {(user as any).job_descriptions && (user as any).job_descriptions.length > 0 && (
                            <div className="col-span-full p-6 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950">
                                <div className="flex items-center gap-2 mb-4 text-slate-600 dark:text-slate-300 text-sm uppercase tracking-wide">
                                    <Briefcase size={16} /> Job Responsibilities
                                </div>
                                <div className="space-y-2">
                                    {(user as any).job_descriptions.slice(0, 3).map((desc: string, idx: number) => (
                                        <p key={idx} className="text-sm text-slate-600 dark:text-slate-400">
                                            • {desc}
                                        </p>
                                    ))}
                                </div>
                            </div>
                        )}
                        <div className="p-6 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950">
                            <div className="flex items-center gap-2 mb-2 text-slate-600 dark:text-slate-300 text-sm uppercase tracking-wide">
                                <Briefcase size={16} /> Current Assignment
                            </div>
                            <p className="text-lg font-semibold text-slate-900 dark:text-slate-100">{user.current_assignment}</p>
                            <p className="text-sm text-slate-500 mt-2">{user.current_focus}</p>
                        </div>
                        <div className="p-6 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950">
                            <div className="flex items-center gap-2 mb-2 text-slate-600 dark:text-slate-300 text-sm uppercase tracking-wide">
                                <GraduationCap size={16} /> Education
                            </div>
                            <p className="text-lg font-semibold text-slate-900 dark:text-slate-100">{user.education?.category}</p>
                            <p className="text-sm text-slate-500 mt-2">{user.education?.branch}</p>
                            <p className="text-xs text-slate-500">{user.education?.field}</p>
                        </div>
                        <div className="p-6 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950">
                            <div className="flex items-center gap-2 mb-2 text-slate-600 dark:text-slate-300 text-sm uppercase tracking-wide">
                                <Award size={16} /> Experience
                            </div>
                            <p className="text-lg font-semibold text-slate-900 dark:text-slate-100">
                                {user.experience_years} yrs
                            </p>
                            <p className="text-sm text-slate-500 mt-2">Grounded in {user.background}</p>
                        </div>
                    </section>

                    {/* Learning Mix */}
                    <section>
                        <h2 className="text-xl font-semibold mb-4">Learning Focus</h2>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div className="p-5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950">
                                <h3 className="text-sm text-slate-500 uppercase tracking-wide mb-3">Recent Courses</h3>
                                <div className="space-y-2">
                                    {(user.recent_courses || []).map((course: { title: string; date?: string; source?: string }, index: number) => (
                                        <div key={`${course.title}-${index}`} className="text-sm">
                                            <p className="font-medium text-slate-900 dark:text-slate-100">{course.title}</p>
                                            <p className="text-xs text-slate-500">{course.date} • {course.source}</p>
                                        </div>
                                    ))}
                                    {!user.recent_courses?.length && (
                                        <p className="text-sm text-slate-500">No recent learning captured.</p>
                                    )}
                                </div>
                            </div>
                            <div className="p-5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950">
                                <h3 className="text-sm text-slate-500 uppercase tracking-wide mb-3">Course Mix</h3>
                                <div className="space-y-3">
                                    {(user.course_mix || []).map((mix: { category: string; share: number }) => (
                                        <div key={mix.category}>
                                            <div className="flex justify-between text-xs text-slate-500 mb-1">
                                                <span>{mix.category}</span>
                                                <span>{mix.share}%</span>
                                            </div>
                                            <div className="w-full bg-slate-100 dark:bg-slate-900 rounded-full h-2 overflow-hidden">
                                                <div className="h-full rounded-full bg-emerald-500" style={{ width: `${mix.share}%` }} />
                                            </div>
                                        </div>
                                    ))}
                                    {!user.course_mix?.length && (
                                        <p className="text-sm text-slate-500">We&rsquo;ll populate this once the user completes courses.</p>
                                    )}
                                </div>
                            </div>
                        </div>
                    </section>
                </>
            )}

            {activeTab === "skills" && (
                <section>
                    <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
                        <Award className="text-emerald-500" /> Skill Profile (&ldquo;Swiss Cheese&rdquo;)
                    </h2>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                        {skills.map((skill) => (
                            <div key={skill.name} className={`p-6 rounded-xl border-2 ${skill.gap ? 'border-dashed border-amber-300 bg-amber-50 dark:bg-amber-900/20 dark:border-amber-700' : 'border-emerald-500 bg-emerald-50 dark:bg-emerald-900/20'} transition-all`}>
                                <div className="flex justify-between items-start mb-2">
                                    <h3 className="font-bold text-lg">{skill.name}</h3>
                                    {skill.gap ? <AlertCircle className="text-amber-500" size={20} /> : <CheckCircle className="text-emerald-500" size={20} />}
                                </div>
                                <p className="text-sm opacity-80 capitalize">{skill.level}</p>
                                {skill.gap && <p className="text-xs text-amber-600 dark:text-amber-400 mt-2 font-medium">Gap Detected</p>}
                            </div>
                        ))}
                    </div>
                </section>
            )}

            {activeTab === "learning" && (
                <section>
                    <h2 className="text-xl font-semibold mb-4">Learning History</h2>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="p-5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950">
                            <h3 className="text-sm text-slate-500 uppercase tracking-wide mb-3">Recent Courses</h3>
                            <div className="space-y-2">
                                {(user.recent_courses || []).map((course: { title: string; date?: string; source?: string }, index: number) => (
                                    <div key={`${course.title}-${index}`} className="text-sm">
                                        <p className="font-medium text-slate-900 dark:text-slate-100">{course.title}</p>
                                        <p className="text-xs text-slate-500">{course.date} • {course.source}</p>
                                    </div>
                                ))}
                                {!user.recent_courses?.length && (
                                    <p className="text-sm text-slate-500">No recent learning captured.</p>
                                )}
                            </div>
                        </div>
                        <div className="p-5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950">
                            <h3 className="text-sm text-slate-500 uppercase tracking-wide mb-3">Completed Courses ({user.completed_courses.length})</h3>
                            <div className="space-y-2 max-h-96 overflow-y-auto">
                                {user.completed_courses.map((course: string, index: number) => (
                                    <div key={index} className="text-sm p-2 bg-slate-50 dark:bg-slate-900 rounded">
                                        <p className="font-medium text-slate-900 dark:text-slate-100">{course}</p>
                                    </div>
                                ))}
                                {!user.completed_courses?.length && (
                                    <p className="text-sm text-slate-500">No completed courses yet.</p>
                                )}
                            </div>
                        </div>
                    </div>
                    <div className="mt-4 p-5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950">
                        <h3 className="text-sm text-slate-500 uppercase tracking-wide mb-3">Course Mix</h3>
                        <div className="space-y-3">
                            {(user.course_mix || []).map((mix: { category: string; share: number }) => (
                                <div key={mix.category}>
                                    <div className="flex justify-between text-xs text-slate-500 mb-1">
                                        <span>{mix.category}</span>
                                        <span>{mix.share}%</span>
                                    </div>
                                    <div className="w-full bg-slate-100 dark:bg-slate-900 rounded-full h-2 overflow-hidden">
                                        <div className="h-full rounded-full bg-emerald-500" style={{ width: `${mix.share}%` }} />
                                    </div>
                                </div>
                            ))}
                            {!user.course_mix?.length && (
                                <p className="text-sm text-slate-500">We&rsquo;ll populate this once the user completes courses.</p>
                            )}
                        </div>
                    </div>
                </section>
            )}

            {activeTab === "assignments" && (
                <>
                    {/* Assigned Modules */}
                    {assignedModulesList.length > 0 && (
                        <section>
                            <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
                                <BookOpen className="text-emerald-500" /> Assigned Modules ({assignedModulesList.length})
                            </h2>
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                                {assignedModulesList.map((assignment) => (
                                    <div key={assignment.courseId} className="bg-white dark:bg-slate-950 p-5 rounded-xl border-2 border-emerald-200 dark:border-emerald-800 hover:shadow-lg transition-all flex flex-col justify-between h-full">
                                        <div>
                                            <div className="flex flex-wrap gap-2 mb-3">
                                                <span className="px-2 py-1 bg-emerald-100 dark:bg-emerald-900 text-emerald-700 dark:text-emerald-300 text-xs rounded-md font-medium capitalize">
                                                    {assignment.course.category}
                                                </span>
                                                <span className={`px-2 py-1 text-xs rounded-md font-medium ${assignment.status === "in-progress"
                                                        ? "bg-amber-100 dark:bg-amber-900 text-amber-700 dark:text-amber-300"
                                                        : assignment.status === "completed"
                                                            ? "bg-emerald-100 dark:bg-emerald-900 text-emerald-700 dark:text-emerald-300"
                                                            : "bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300"
                                                    }`}>
                                                    {assignment.status === "in-progress"
                                                        ? "In Progress"
                                                        : assignment.status === "completed"
                                                            ? "Completed"
                                                            : "Assigned"}
                                                </span>
                                            </div>
                                            <h3 className="font-semibold text-slate-900 dark:text-slate-100 mb-2 line-clamp-2">
                                                {assignment.courseTitle}
                                            </h3>
                                            <p className="text-sm text-slate-500 dark:text-slate-400 line-clamp-2 mb-3">
                                                {assignment.course.topic || assignment.course.source}
                                            </p>
                                            <div className="flex items-center gap-2 text-xs text-slate-500">
                                                <Clock size={14} />
                                                <span>
                                                    Assigned {new Date(assignment.assignedDate).toLocaleDateString()}
                                                </span>
                                            </div>
                                        </div>
                                        <div className="flex gap-2 mt-4 pt-4 border-t border-slate-200 dark:border-slate-800">
                                            <button
                                                onClick={() => handleUnassignModule(assignment.courseTitle)}
                                                className="flex-1 py-2 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 rounded-lg font-medium hover:bg-red-100 dark:hover:bg-red-900/30 transition-colors flex items-center justify-center gap-2"
                                            >
                                                <X size={16} /> Unassign
                                            </button>
                                            <button
                                                onClick={() => {
                                                    if (assignment.status === "assigned") {
                                                        setAssignedModules((prev) =>
                                                            prev.map((m) =>
                                                                m.courseTitle === assignment.courseTitle
                                                                    ? { ...m, status: "in-progress" as const }
                                                                    : m
                                                            )
                                                        );
                                                        setActiveModule(assignment.course);
                                                        toast.success("Module Started", {
                                                            description: `"${assignment.courseTitle}" is now in progress.`,
                                                            duration: 3000,
                                                        });
                                                    } else if (assignment.status === "in-progress") {
                                                        setActiveModule(assignment.course);
                                                    }
                                                }}
                                                className={`flex-1 py-2 rounded-lg font-medium transition-colors flex items-center justify-center gap-2 ${assignment.status === "in-progress"
                                                        ? "bg-amber-500 text-white hover:bg-amber-600"
                                                        : assignment.status === "completed"
                                                            ? "bg-emerald-600 text-white hover:bg-emerald-700"
                                                            : "bg-emerald-600 text-white hover:bg-emerald-700"
                                                    }`}
                                            >
                                                {assignment.status === "in-progress" ? (
                                                    <>
                                                        <Loader2 size={16} className="animate-spin" /> Continue
                                                    </>
                                                ) : assignment.status === "completed" ? (
                                                    <>
                                                        <CheckCircle size={16} /> Completed
                                                    </>
                                                ) : (
                                                    <>
                                                        <Play size={16} /> Start
                                                    </>
                                                )}
                                            </button>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </section>
                    )}

                    {/* Recommendations */}
                    <section>
                        <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
                            <BookOpen className="text-blue-500" /> Recommended Micro-Modules
                        </h2>
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                            {recommendations.map((course: Course, index: number) => (
                                <div key={`${course.title}-${index}`} className="bg-white dark:bg-slate-950 p-5 rounded-xl border border-slate-200 dark:border-slate-800 hover:shadow-lg transition-all flex flex-col justify-between h-full">
                                    <div>
                                        <div className="flex flex-wrap gap-2 mb-3">
                                            <span className="px-2 py-1 bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 text-xs rounded-md font-medium capitalize">{course.category}</span>
                                            {course.provider && (
                                                <span className="px-2 py-1 bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 text-xs rounded-md font-medium">{course.provider}</span>
                                            )}
                                        </div>
                                        <h3 className="font-semibold text-slate-900 dark:text-slate-100 mb-2 line-clamp-2">{course.title}</h3>
                                        <p className="text-sm text-slate-500 dark:text-slate-400 line-clamp-3 mb-4">{course.topic || course.source}</p>
                                    </div>
                                    <button
                                        onClick={() => handleAssignModule(course)}
                                        disabled={isModuleAssigned(course.title)}
                                        className={`w-full py-2 rounded-lg font-medium transition-opacity flex items-center justify-center gap-2 ${isModuleAssigned(course.title)
                                                ? "bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-400 cursor-not-allowed"
                                                : "bg-slate-900 dark:bg-slate-100 text-white dark:text-slate-900 hover:opacity-90"
                                            }`}
                                    >
                                        {isModuleAssigned(course.title) ? (
                                            <>
                                                <Check size={16} /> Assigned
                                            </>
                                        ) : (
                                            <>
                                                <Play size={16} /> Assign Module
                                            </>
                                        )}
                                    </button>
                                </div>
                            ))}
                            {recommendations.length === 0 && (
                                <div className="col-span-full text-center py-12 text-slate-500 bg-slate-50 dark:bg-slate-900 rounded-xl border border-dashed border-slate-300 dark:border-slate-700">
                                    No specific gaps found requiring immediate intervention.
                                </div>
                            )}
                        </div>
                    </section>
                </>
            )}

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
                                onClick={() => {
                                    setAssignedModules((prev) =>
                                        prev.map((m) =>
                                            m.courseTitle === activeModule.title
                                                ? { ...m, status: "completed" as const }
                                                : m
                                        )
                                    );
                                    toast.success("Module Completed!", {
                                        description: `"${activeModule.title}" has been marked as completed.`,
                                        duration: 3000,
                                    });
                                    setActiveModule(null);
                                }}
                                className="flex-1 py-3 bg-emerald-600 text-white rounded-lg font-medium hover:bg-emerald-700 transition-colors flex items-center justify-center gap-2"
                            >
                                <CheckCircle size={20} /> Mark as Completed
                            </button>
                            <button
                                onClick={() => setActiveModule(null)}
                                className="px-6 py-3 bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 rounded-lg font-medium hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors"
                            >
                                Close
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
