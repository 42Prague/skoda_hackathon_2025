"use client";

import { Users, AlertTriangle } from "lucide-react";
import Link from "next/link";
import usersData from "@/data/users.json";

export default function DepartmentOverviewPage() {
    // Aggregate data by department
    const departments: Record<string, { count: number; gaps: number; skills: Record<string, number> }> = {};

    usersData.forEach(user => {
        if (!departments[user.department]) {
            departments[user.department] = { count: 0, gaps: 0, skills: {} };
        }

        const dept = departments[user.department];
        dept.count++;

        // Calculate health based on average skill level
        // Beginner = 1, Intermediate = 2, Advanced = 3
        // Max score = 3 * number of skills
        const skillLevels: Record<string, number> = { "beginner": 1, "intermediate": 2, "advanced": 3 };
        let totalScore = 0;
        let maxPossibleScore = 0;

        Object.values(user.skills).forEach((level: any) => {
            totalScore += skillLevels[level.toLowerCase()] || 0;
            maxPossibleScore += 3;
        });

        // If average score is below 2 (Intermediate), consider it a "gap"
        const health = maxPossibleScore > 0 ? (totalScore / maxPossibleScore) : 0;
        if (health < 0.66) dept.gaps++; // Less than 66% health is a gap

        // Store cumulative health for averaging later
        if (!dept.skills.health) dept.skills.health = 0;
        dept.skills.health += health;
    });

    return (
        <div className="space-y-8">
            <div className="flex items-center gap-3">
                <h1 className="text-3xl font-bold text-slate-900 dark:text-slate-100">Department Overview</h1>
                <div className="group relative">
                    <div className="p-2 rounded-full hover:bg-slate-100 dark:hover:bg-slate-800 cursor-help transition-colors text-slate-400 hover:text-emerald-600">
                        <Users size={20} />
                    </div>
                    {/* Tooltip fixed position */}
                    <div className="absolute left-0 top-full mt-2 w-72 p-4 bg-slate-900 text-white text-sm rounded-xl shadow-xl opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-50 pointer-events-none">
                        <p className="font-semibold mb-1">Strategic Heat Map</p>
                        <p className="text-slate-300 leading-relaxed">
                            Visualize skill health across your organization. Identify "Critical Gaps" to allocate training budget effectively.
                            <br /><br />
                            <strong>Click a department</strong> to drill down into specific employees.
                        </p>
                    </div>
                </div>
            </div>

            <div className="flex flex-wrap justify-center gap-6">
                {Object.entries(departments).map(([name, data]) => (
                    <Link
                        key={name}
                        href={`/?q=${encodeURIComponent(name)}`}
                        className="w-full md:w-[calc(50%-12px)] lg:w-[calc(33.333%-16px)] block"
                    >
                        <div className="bg-white dark:bg-slate-950 p-6 rounded-xl border border-slate-200 dark:border-slate-800 hover:shadow-lg hover:border-emerald-500 transition-all cursor-pointer group h-full">
                            <div className="flex justify-between items-start mb-4">
                                <div className="p-3 bg-emerald-100 dark:bg-emerald-900/30 rounded-lg text-emerald-600 dark:text-emerald-400 group-hover:scale-110 transition-transform">
                                    <Users size={24} />
                                </div>
                                <span className="text-xs font-medium px-2 py-1 bg-slate-100 dark:bg-slate-800 rounded-full text-slate-600 dark:text-slate-400">
                                    {data.count} Employees
                                </span>
                            </div>

                            <h3 className="text-xl font-bold text-slate-900 dark:text-slate-100 mb-2">{name}</h3>

                            <div className="space-y-3">
                                <div className="flex justify-between items-center text-sm">
                                    <span className="text-slate-500">Skill Health</span>
                                    <span className="font-medium text-emerald-600">
                                        {Math.round((data.skills.health / data.count) * 100)}%
                                    </span>
                                </div>
                                <div className="w-full bg-slate-100 dark:bg-slate-800 rounded-full h-2 overflow-hidden">
                                    <div
                                        className="bg-emerald-500 h-full rounded-full"
                                        style={{ width: `${(data.skills.health / data.count) * 100}%` }}
                                    ></div>
                                </div>

                                <div className="pt-4 flex items-center gap-2 text-amber-600 dark:text-amber-400 text-sm">
                                    <AlertTriangle size={16} />
                                    <span>{data.gaps} employees have critical gaps</span>
                                </div>
                            </div>
                        </div>
                    </Link>
                ))}
            </div>
        </div>
    );
}
