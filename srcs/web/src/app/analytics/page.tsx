"use client";

import { useState, useMemo } from "react";
import Link from "next/link";
import {
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    Legend,
    ResponsiveContainer,
    PieChart,
    Pie,
    Cell,
    AreaChart,
    Area,
    LineChart,
    Line,
} from "recharts";
import usersData from "@/data/users.json";
import coursesData from "@/data/courses.json";

// --- Types ---
type User = typeof usersData[0];

// --- Colors ---
const COLORS = ["#10b981", "#3b82f6", "#f59e0b", "#ef4444", "#8b5cf6", "#ec4899", "#6366f1"];

export default function AnalyticsPage() {
    const [activeTab, setActiveTab] = useState<"overview" | "skills" | "learning" | "departments">("overview");

    // --- Data Processing ---
    const departmentData = useMemo(() => {
        const counts: Record<string, number> = {};
        usersData.forEach((user) => {
            const dept = user.department || "Unknown";
            counts[dept] = (counts[dept] || 0) + 1;
        });
        return Object.entries(counts)
            .map(([name, value]) => ({ name, value }))
            .sort((a, b) => b.value - a.value);
    }, []);

    const skillData = useMemo(() => {
        const counts: Record<string, number> = {};
        const skillLevels: Record<string, { total: number; advanced: number; intermediate: number; beginner: number }> = {};
        
        usersData.forEach((user) => {
            Object.entries(user.skills).forEach(([skill, level]: [string, any]) => {
                counts[skill] = (counts[skill] || 0) + 1;
                if (!skillLevels[skill]) {
                    skillLevels[skill] = { total: 0, advanced: 0, intermediate: 0, beginner: 0 };
                }
                skillLevels[skill].total++;
                const levelLower = level?.toLowerCase() || "beginner";
                if (levelLower === "advanced") skillLevels[skill].advanced++;
                else if (levelLower === "intermediate") skillLevels[skill].intermediate++;
                else skillLevels[skill].beginner++;
            });
        });
        
        return {
            topSkills: Object.entries(counts)
                .map(([name, value]) => ({ name, value }))
                .sort((a, b) => b.value - a.value)
                .slice(0, 10),
            skillLevels: Object.entries(skillLevels)
                .map(([name, levels]) => ({
                    name,
                    ...levels,
                    advancedPercent: Math.round((levels.advanced / levels.total) * 100),
                }))
                .sort((a, b) => b.total - a.total)
                .slice(0, 10),
        };
    }, []);

    const learningTrendsData = useMemo(() => {
        const months: Record<string, number> = {};
        usersData.forEach(user => {
            user.recent_courses.forEach(course => {
                if (course.date) {
                    const date = new Date(course.date);
                    const month = date.toLocaleString('default', { month: 'short' });
                    months[month] = (months[month] || 0) + 1;
                }
            });
        });
        const monthOrder = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
        return Object.entries(months)
            .map(([month, count]) => ({ month, courses: count }))
            .sort((a, b) => monthOrder.indexOf(a.month) - monthOrder.indexOf(b.month));
    }, []);

    const courseCategoryData = useMemo(() => {
        const counts: Record<string, number> = {};
        coursesData.forEach(course => {
            const cat = course.category || "Uncategorized";
            counts[cat] = (counts[cat] || 0) + 1;
        });
        return Object.entries(counts)
            .map(([name, value]) => ({ name, value }))
            .sort((a, b) => b.value - a.value);
    }, []);

    const departmentSkillHealth = useMemo(() => {
        const deptHealth: Record<string, { count: number; totalHealth: number; skills: Record<string, number> }> = {};
        
        usersData.forEach(user => {
            const dept = user.department || "Unknown";
            if (!deptHealth[dept]) {
                deptHealth[dept] = { count: 0, totalHealth: 0, skills: {} };
            }
            
            deptHealth[dept].count++;
            const skillLevels: Record<string, number> = { "beginner": 1, "intermediate": 2, "advanced": 3 };
            let totalScore = 0;
            let maxScore = 0;
            
            Object.values(user.skills).forEach((level: any) => {
                totalScore += skillLevels[level?.toLowerCase()] || 0;
                maxScore += 3;
            });
            
            const health = maxScore > 0 ? (totalScore / maxScore) : 0;
            deptHealth[dept].totalHealth += health;
        });
        
        return Object.entries(deptHealth).map(([name, data]) => ({
            name,
            health: Math.round((data.totalHealth / data.count) * 100),
            employees: data.count,
        })).sort((a, b) => b.health - a.health);
    }, []);

    const topLearners = useMemo(() => {
        return [...usersData]
            .sort((a, b) => b.completed_courses.length - a.completed_courses.length)
            .slice(0, 10)
            .map(user => ({
                id: user.id,
                name: user.name,
                department: user.department,
                count: user.completed_courses.length,
                experience: user.experience_years || 0,
            }));
    }, []);

    const popularCourses = useMemo(() => {
        const counts: Record<string, number> = {};
        usersData.forEach(user => {
            user.completed_courses.forEach(course => {
                counts[course] = (counts[course] || 0) + 1;
            });
        });
        return Object.entries(counts)
            .map(([name, value]) => ({ name, value }))
            .sort((a, b) => b.value - a.value)
            .slice(0, 10);
    }, []);

    const totalCoursesCompleted = useMemo(() => {
        return usersData.reduce((sum, user) => sum + user.completed_courses.length, 0);
    }, []);

    const averageCoursesPerUser = useMemo(() => {
        return usersData.length > 0 ? Math.round((totalCoursesCompleted / usersData.length) * 10) / 10 : 0;
    }, [totalCoursesCompleted]);

    const tabs = [
        { id: "overview" as const, label: "Overview", icon: "📊" },
        { id: "skills" as const, label: "Skills", icon: "🎯" },
        { id: "learning" as const, label: "Learning", icon: "📚" },
        { id: "departments" as const, label: "Departments", icon: "🏢" },
    ];

    return (
        <div className="p-8 max-w-7xl mx-auto space-y-8">
            <div className="flex flex-col gap-2">
                <h1 className="text-3xl font-bold text-slate-900 dark:text-white">Analytics Dashboard</h1>
                <p className="text-slate-500 dark:text-slate-400">
                    Comprehensive insights into workforce skills, learning trends, and department performance.
                </p>
            </div>

            {/* Tabs */}
            <div className="flex gap-2 border-b border-slate-200 dark:border-slate-800">
                {tabs.map((tab) => (
                    <button
                        key={tab.id}
                        onClick={() => setActiveTab(tab.id)}
                        className={`px-6 py-3 font-medium transition-colors border-b-2 ${
                            activeTab === tab.id
                                ? "border-emerald-500 text-emerald-600 dark:text-emerald-400"
                                : "border-transparent text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-300"
                        }`}
                    >
                        <span className="mr-2">{tab.icon}</span>
                        {tab.label}
                    </button>
                ))}
            </div>

            {/* Key Metrics - Always Visible */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                <div className="bg-white dark:bg-slate-900 p-6 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm">
                    <h3 className="text-sm font-medium text-slate-500 dark:text-slate-400">Total Employees</h3>
                    <p className="text-3xl font-bold text-slate-900 dark:text-white mt-2">{usersData.length}</p>
                </div>
                <div className="bg-white dark:bg-slate-900 p-6 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm">
                    <h3 className="text-sm font-medium text-slate-500 dark:text-slate-400">Total Courses</h3>
                    <p className="text-3xl font-bold text-slate-900 dark:text-white mt-2">{coursesData.length.toLocaleString()}</p>
                </div>
                <div className="bg-white dark:bg-slate-900 p-6 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm">
                    <h3 className="text-sm font-medium text-slate-500 dark:text-slate-400">Courses Completed</h3>
                    <p className="text-3xl font-bold text-emerald-600 dark:text-emerald-400 mt-2">{totalCoursesCompleted.toLocaleString()}</p>
                </div>
                <div className="bg-white dark:bg-slate-900 p-6 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm">
                    <h3 className="text-sm font-medium text-slate-500 dark:text-slate-400">Avg. per Employee</h3>
                    <p className="text-3xl font-bold text-slate-900 dark:text-white mt-2">{averageCoursesPerUser}</p>
                </div>
            </div>

            {/* Tab Content */}
            {activeTab === "overview" && (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                    <div className="bg-white dark:bg-slate-900 p-6 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm">
                        <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-6">Department Distribution</h3>
                        <div className="h-[300px] w-full">
                            <ResponsiveContainer width="100%" height="100%">
                                <PieChart>
                                    <Pie
                                        data={departmentData}
                                        cx="50%"
                                        cy="50%"
                                        innerRadius={60}
                                        outerRadius={100}
                                        fill="#8884d8"
                                        paddingAngle={5}
                                        dataKey="value"
                                    >
                                        {departmentData.map((entry, index) => (
                                            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                        ))}
                                    </Pie>
                                    <Tooltip
                                        contentStyle={{ backgroundColor: 'rgba(255, 255, 255, 0.9)', borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                                        itemStyle={{ color: '#1e293b' }}
                                    />
                                    <Legend />
                                </PieChart>
                            </ResponsiveContainer>
                        </div>
                    </div>

                    <div className="bg-white dark:bg-slate-900 p-6 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm">
                        <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-6">Top 10 Skills</h3>
                        <div className="h-[300px] w-full">
                            <ResponsiveContainer width="100%" height="100%">
                                <BarChart data={skillData.topSkills} layout="vertical" margin={{ top: 5, right: 30, left: 40, bottom: 5 }}>
                                    <CartesianGrid strokeDasharray="3 3" horizontal={true} vertical={false} stroke="#e2e8f0" />
                                    <XAxis type="number" hide />
                                    <YAxis
                                        dataKey="name"
                                        type="category"
                                        width={120}
                                        tick={{ fontSize: 12, fill: '#64748b' }}
                                    />
                                    <Tooltip
                                        cursor={{ fill: 'transparent' }}
                                        contentStyle={{ backgroundColor: 'rgba(255, 255, 255, 0.9)', borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                                        itemStyle={{ color: '#1e293b' }}
                                    />
                                    <Bar dataKey="value" fill="#10b981" radius={[0, 4, 4, 0]} barSize={20} />
                                </BarChart>
                            </ResponsiveContainer>
                        </div>
                    </div>

                    <div className="col-span-1 lg:col-span-2 bg-white dark:bg-slate-900 p-6 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm">
                        <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-6">Learning Activity Trends</h3>
                        <div className="h-[300px] w-full">
                            <ResponsiveContainer width="100%" height="100%">
                                <AreaChart data={learningTrendsData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                                    <defs>
                                        <linearGradient id="colorHours" x1="0" y1="0" x2="0" y2="1">
                                            <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.8} />
                                            <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                                        </linearGradient>
                                    </defs>
                                    <XAxis dataKey="month" stroke="#94a3b8" tick={{ fontSize: 12 }} />
                                    <YAxis stroke="#94a3b8" tick={{ fontSize: 12 }} />
                                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                                    <Tooltip
                                        contentStyle={{ backgroundColor: 'rgba(255, 255, 255, 0.9)', borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                                        itemStyle={{ color: '#1e293b' }}
                                    />
                                    <Area type="monotone" dataKey="courses" stroke="#3b82f6" fillOpacity={1} fill="url(#colorHours)" />
                                </AreaChart>
                            </ResponsiveContainer>
                        </div>
                    </div>
                </div>
            )}

            {activeTab === "skills" && (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                    <div className="bg-white dark:bg-slate-900 p-6 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm">
                        <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-6">Top Skills Distribution</h3>
                        <div className="h-[400px] w-full">
                            <ResponsiveContainer width="100%" height="100%">
                                <BarChart data={skillData.topSkills} layout="vertical" margin={{ top: 5, right: 30, left: 40, bottom: 5 }}>
                                    <CartesianGrid strokeDasharray="3 3" horizontal={true} vertical={false} stroke="#e2e8f0" />
                                    <XAxis type="number" />
                                    <YAxis
                                        dataKey="name"
                                        type="category"
                                        width={150}
                                        tick={{ fontSize: 11, fill: '#64748b' }}
                                    />
                                    <Tooltip
                                        cursor={{ fill: 'transparent' }}
                                        contentStyle={{ backgroundColor: 'rgba(255, 255, 255, 0.9)', borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                                        itemStyle={{ color: '#1e293b' }}
                                    />
                                    <Bar dataKey="value" fill="#10b981" radius={[0, 4, 4, 0]} barSize={20} />
                                </BarChart>
                            </ResponsiveContainer>
                        </div>
                    </div>

                    <div className="bg-white dark:bg-slate-900 p-6 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm">
                        <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-6">Skill Proficiency Levels</h3>
                        <div className="space-y-4">
                            {skillData.skillLevels.map((skill, index) => (
                                <div key={skill.name} className="space-y-2">
                                    <div className="flex justify-between text-sm">
                                        <span className="font-medium text-slate-900 dark:text-white">{skill.name}</span>
                                        <span className="text-slate-500">{skill.advancedPercent}% Advanced</span>
                                    </div>
                                    <div className="w-full bg-slate-100 dark:bg-slate-800 rounded-full h-2 overflow-hidden">
                                        <div className="flex h-full">
                                            <div className="bg-emerald-600" style={{ width: `${skill.advancedPercent}%` }}></div>
                                            <div className="bg-amber-500" style={{ width: `${Math.round((skill.intermediate / skill.total) * 100)}%` }}></div>
                                            <div className="bg-slate-400" style={{ width: `${Math.round((skill.beginner / skill.total) * 100)}%` }}></div>
                                        </div>
                                    </div>
                                    <div className="flex gap-4 text-xs text-slate-500">
                                        <span>Advanced: {skill.advanced}</span>
                                        <span>Intermediate: {skill.intermediate}</span>
                                        <span>Beginner: {skill.beginner}</span>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            )}

            {activeTab === "learning" && (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                    <div className="bg-white dark:bg-slate-900 p-6 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm">
                        <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-6">🏆 Top Learners</h3>
                        <div className="space-y-3">
                            {topLearners.map((learner, index) => (
                                <Link key={learner.id} href={`/employee/${learner.id}`}>
                                    <div className="flex items-center justify-between p-3 bg-slate-50 dark:bg-slate-800/50 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors cursor-pointer group">
                                        <div className="flex items-center gap-3">
                                            <div className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-sm ${index === 0 ? "bg-yellow-100 text-yellow-700" :
                                                index === 1 ? "bg-slate-200 text-slate-700" :
                                                    index === 2 ? "bg-amber-100 text-amber-800" :
                                                        "bg-slate-100 text-slate-500"
                                                }`}>
                                                {index + 1}
                                            </div>
                                            <div>
                                                <p className="font-medium text-slate-900 dark:text-white text-sm group-hover:text-emerald-600 transition-colors">{learner.name}</p>
                                                <p className="text-xs text-slate-500">{learner.department} • {learner.experience} yrs</p>
                                            </div>
                                        </div>
                                        <div className="text-right">
                                            <span className="block font-bold text-emerald-600 dark:text-emerald-400">{learner.count}</span>
                                            <span className="text-[10px] text-slate-400 uppercase">Courses</span>
                                        </div>
                                    </div>
                                </Link>
                            ))}
                        </div>
                    </div>

                    <div className="bg-white dark:bg-slate-900 p-6 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm">
                        <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-6">🔥 Most Popular Courses</h3>
                        <div className="h-[400px] w-full">
                            <ResponsiveContainer width="100%" height="100%">
                                <BarChart data={popularCourses} layout="vertical" margin={{ top: 5, right: 30, left: 10, bottom: 5 }}>
                                    <CartesianGrid strokeDasharray="3 3" horizontal={true} vertical={false} stroke="#e2e8f0" />
                                    <XAxis type="number" />
                                    <YAxis
                                        dataKey="name"
                                        type="category"
                                        width={200}
                                        tick={{ fontSize: 10, fill: '#64748b' }}
                                    />
                                    <Tooltip
                                        cursor={{ fill: 'transparent' }}
                                        contentStyle={{ backgroundColor: 'rgba(255, 255, 255, 0.9)', borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                                        itemStyle={{ color: '#1e293b' }}
                                    />
                                    <Bar dataKey="value" fill="#f59e0b" radius={[0, 4, 4, 0]} barSize={20} />
                                </BarChart>
                            </ResponsiveContainer>
                        </div>
                    </div>

                    <div className="col-span-1 lg:col-span-2 bg-white dark:bg-slate-900 p-6 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm">
                        <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-6">Course Categories</h3>
                        <div className="h-[300px] w-full">
                            <ResponsiveContainer width="100%" height="100%">
                                <BarChart data={courseCategoryData} margin={{ top: 5, right: 30, left: 0, bottom: 5 }}>
                                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                                    <XAxis
                                        dataKey="name"
                                        angle={-45}
                                        textAnchor="end"
                                        height={100}
                                        tick={{ fontSize: 11, fill: '#64748b' }}
                                    />
                                    <YAxis stroke="#94a3b8" tick={{ fontSize: 12 }} />
                                    <Tooltip
                                        contentStyle={{ backgroundColor: 'rgba(255, 255, 255, 0.9)', borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                                        itemStyle={{ color: '#1e293b' }}
                                    />
                                    <Bar dataKey="value" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
                                </BarChart>
                            </ResponsiveContainer>
                        </div>
                    </div>
                </div>
            )}

            {activeTab === "departments" && (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                    <div className="col-span-1 lg:col-span-2 bg-white dark:bg-slate-900 p-6 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm">
                        <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-6">Department Skill Health</h3>
                        <div className="h-[400px] w-full">
                            <ResponsiveContainer width="100%" height="100%">
                                <BarChart data={departmentSkillHealth} margin={{ top: 5, right: 30, left: 0, bottom: 5 }}>
                                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                                    <XAxis
                                        dataKey="name"
                                        angle={-45}
                                        textAnchor="end"
                                        height={100}
                                        tick={{ fontSize: 11, fill: '#64748b' }}
                                    />
                                    <YAxis stroke="#94a3b8" tick={{ fontSize: 12 }} domain={[0, 100]} />
                                    <Tooltip
                                        contentStyle={{ backgroundColor: 'rgba(255, 255, 255, 0.9)', borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                                        itemStyle={{ color: '#1e293b' }}
                                    />
                                    <Bar dataKey="health" fill="#10b981" radius={[4, 4, 0, 0]}>
                                        {departmentSkillHealth.map((entry, index) => (
                                            <Cell key={`cell-${index}`} fill={entry.health >= 70 ? "#10b981" : entry.health >= 50 ? "#f59e0b" : "#ef4444"} />
                                        ))}
                                    </Bar>
                                </BarChart>
                            </ResponsiveContainer>
                        </div>
                    </div>

                    <div className="bg-white dark:bg-slate-900 p-6 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm">
                        <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-6">Department Overview</h3>
                        <div className="space-y-4">
                            {departmentSkillHealth.map((dept) => (
                                <Link key={dept.name} href={`/?q=${encodeURIComponent(dept.name)}`}>
                                    <div className="p-4 bg-slate-50 dark:bg-slate-800/50 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors cursor-pointer">
                                        <div className="flex justify-between items-center mb-2">
                                            <h4 className="font-semibold text-slate-900 dark:text-white">{dept.name}</h4>
                                            <span className={`px-2 py-1 rounded text-xs font-medium ${
                                                dept.health >= 70 ? "bg-emerald-100 text-emerald-700" :
                                                dept.health >= 50 ? "bg-amber-100 text-amber-700" :
                                                "bg-red-100 text-red-700"
                                            }`}>
                                                {dept.health}%
                                            </span>
                                        </div>
                                        <div className="w-full bg-slate-200 dark:bg-slate-700 rounded-full h-2 overflow-hidden">
                                            <div
                                                className={`h-full rounded-full ${
                                                    dept.health >= 70 ? "bg-emerald-500" :
                                                    dept.health >= 50 ? "bg-amber-500" :
                                                    "bg-red-500"
                                                }`}
                                                style={{ width: `${dept.health}%` }}
                                            ></div>
                                        </div>
                                        <p className="text-xs text-slate-500 mt-2">{dept.employees} employees</p>
                                    </div>
                                </Link>
                            ))}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
