"use client";

import { BookOpen, FileText, HelpCircle, Info, Lightbulb, Target, Users } from "lucide-react";

export default function DocumentationPage() {
    return (
        <div className="p-8 max-w-5xl mx-auto space-y-8">
            <div className="flex flex-col gap-2">
                <h1 className="text-3xl font-bold text-slate-900 dark:text-white flex items-center gap-3">
                    <BookOpen className="text-emerald-500" size={32} />
                    Documentation & Help
                </h1>
                <p className="text-slate-500 dark:text-slate-400">
                    Learn about the AI Skill Coach platform, data model, and guidelines.
                </p>
            </div>

            {/* Quick Links */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <a href="#overview" className="p-4 bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 hover:shadow-lg transition-all cursor-pointer">
                    <Info className="text-emerald-500 mb-2" size={24} />
                    <h3 className="font-semibold text-slate-900 dark:text-white mb-1">Overview</h3>
                    <p className="text-sm text-slate-500 dark:text-slate-400">Platform introduction</p>
                </a>
                <a href="#data-model" className="p-4 bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 hover:shadow-lg transition-all cursor-pointer">
                    <FileText className="text-emerald-500 mb-2" size={24} />
                    <h3 className="font-semibold text-slate-900 dark:text-white mb-1">Data Model</h3>
                    <p className="text-sm text-slate-500 dark:text-slate-400">Understanding the data</p>
                </a>
                <a href="#guidelines" className="p-4 bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 hover:shadow-lg transition-all cursor-pointer">
                    <Target className="text-emerald-500 mb-2" size={24} />
                    <h3 className="font-semibold text-slate-900 dark:text-white mb-1">Guidelines</h3>
                    <p className="text-sm text-slate-500 dark:text-slate-400">Best practices</p>
                </a>
            </div>

            {/* Overview Section */}
            <section id="overview" className="bg-white dark:bg-slate-900 p-6 rounded-xl border border-slate-200 dark:border-slate-800">
                <h2 className="text-2xl font-semibold text-slate-900 dark:text-white mb-4 flex items-center gap-2">
                    <Info className="text-emerald-500" size={24} />
                    Platform Overview
                </h2>
                <div className="space-y-4 text-slate-600 dark:text-slate-400">
                    <p>
                        The AI Skill Coach is a comprehensive learning and development platform designed for Škoda Auto employees. 
                        It provides personalized skill assessments, course recommendations, and learning tracking.
                    </p>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
                        <div className="p-4 bg-slate-50 dark:bg-slate-800 rounded-lg">
                            <Users className="text-emerald-500 mb-2" size={20} />
                            <h4 className="font-semibold text-slate-900 dark:text-white mb-1">Employee Profiles</h4>
                            <p className="text-sm">View detailed employee profiles with skills, learning history, and recommendations.</p>
                        </div>
                        <div className="p-4 bg-slate-50 dark:bg-slate-800 rounded-lg">
                            <BookOpen className="text-emerald-500 mb-2" size={20} />
                            <h4 className="font-semibold text-slate-900 dark:text-white mb-1">Course Catalog</h4>
                            <p className="text-sm">Access thousands of courses across multiple categories and providers.</p>
                        </div>
                        <div className="p-4 bg-slate-50 dark:bg-slate-800 rounded-lg">
                            <Target className="text-emerald-500 mb-2" size={20} />
                            <h4 className="font-semibold text-slate-900 dark:text-white mb-1">Skill Assessment</h4>
                            <p className="text-sm">Identify skill gaps and receive personalized learning recommendations.</p>
                        </div>
                        <div className="p-4 bg-slate-50 dark:bg-slate-800 rounded-lg">
                            <Lightbulb className="text-emerald-500 mb-2" size={20} />
                            <h4 className="font-semibold text-slate-900 dark:text-white mb-1">Analytics</h4>
                            <p className="text-sm">Track learning progress and department-wide skill development.</p>
                        </div>
                    </div>
                </div>
            </section>

            {/* Data Model Section */}
            <section id="data-model" className="bg-white dark:bg-slate-900 p-6 rounded-xl border border-slate-200 dark:border-slate-800">
                <h2 className="text-2xl font-semibold text-slate-900 dark:text-white mb-4 flex items-center gap-2">
                    <FileText className="text-emerald-500" size={24} />
                    Data Model
                </h2>
                <div className="space-y-4 text-slate-600 dark:text-slate-400">
                    <p>
                        The platform uses comprehensive data from multiple sources to provide accurate skill assessments and recommendations:
                    </p>
                    <div className="space-y-3 mt-4">
                        <div className="p-4 bg-slate-50 dark:bg-slate-800 rounded-lg">
                            <h4 className="font-semibold text-slate-900 dark:text-white mb-2">Employee Data</h4>
                            <ul className="text-sm space-y-1 list-disc list-inside">
                                <li>Personal information and organizational hierarchy</li>
                                <li>Education background and professional experience</li>
                                <li>Current role and department assignments</li>
                                <li>Job descriptions and responsibilities</li>
                            </ul>
                        </div>
                        <div className="p-4 bg-slate-50 dark:bg-slate-800 rounded-lg">
                            <h4 className="font-semibold text-slate-900 dark:text-white mb-2">Learning Data</h4>
                            <ul className="text-sm space-y-1 list-disc list-inside">
                                <li>Training history from Legacy LMS (ZHRPD_VZD_STA_007)</li>
                                <li>Extended training records (ZHRPD_VZD_STA_016)</li>
                                <li>Degreed platform course completions</li>
                                <li>Skill mapping and competency data</li>
                            </ul>
                        </div>
                        <div className="p-4 bg-slate-50 dark:bg-slate-800 rounded-lg">
                            <h4 className="font-semibold text-slate-900 dark:text-white mb-2">Course Data</h4>
                            <ul className="text-sm space-y-1 list-disc list-inside">
                                <li>Course titles, descriptions, and metadata</li>
                                <li>Multi-language support (English, Czech, German)</li>
                                <li>Course categories and skill mappings</li>
                                <li>Provider information and content types</li>
                            </ul>
                        </div>
                        <div className="p-4 bg-slate-50 dark:bg-slate-800 rounded-lg">
                            <h4 className="font-semibold text-slate-900 dark:text-white mb-2">Organizational Data</h4>
                            <ul className="text-sm space-y-1 list-disc list-inside">
                                <li>Department hierarchy and structure</li>
                                <li>Job descriptions and role definitions</li>
                                <li>Skill requirements by position</li>
                            </ul>
                        </div>
                    </div>
                </div>
            </section>

            {/* Guidelines Section */}
            <section id="guidelines" className="bg-white dark:bg-slate-900 p-6 rounded-xl border border-slate-200 dark:border-slate-800">
                <h2 className="text-2xl font-semibold text-slate-900 dark:text-white mb-4 flex items-center gap-2">
                    <Target className="text-emerald-500" size={24} />
                    Guidelines & Best Practices
                </h2>
                <div className="space-y-4 text-slate-600 dark:text-slate-400">
                    <div className="space-y-3">
                        <div className="p-4 bg-emerald-50 dark:bg-emerald-900/20 border border-emerald-200 dark:border-emerald-800 rounded-lg">
                            <h4 className="font-semibold text-emerald-900 dark:text-emerald-100 mb-2">For HR Managers</h4>
                            <ul className="text-sm space-y-1 list-disc list-inside text-emerald-800 dark:text-emerald-200">
                                <li>Use the Analytics dashboard to identify department-wide skill gaps</li>
                                <li>Assign relevant courses to employees based on their skill profiles</li>
                                <li>Monitor learning progress and completion rates</li>
                                <li>Leverage the "Swiss Cheese" skill profile to understand individual strengths and gaps</li>
                            </ul>
                        </div>
                        <div className="p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
                            <h4 className="font-semibold text-blue-900 dark:text-blue-100 mb-2">For Employees</h4>
                            <ul className="text-sm space-y-1 list-disc list-inside text-blue-800 dark:text-blue-200">
                                <li>Review your skill profile regularly to identify development areas</li>
                                <li>Explore the Daily Micro-Challenges feed for quick learning opportunities</li>
                                <li>Complete assigned modules and track your progress</li>
                                <li>Use the search functionality to find courses relevant to your role</li>
                            </ul>
                        </div>
                        <div className="p-4 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg">
                            <h4 className="font-semibold text-amber-900 dark:text-amber-100 mb-2">Skill Assessment</h4>
                            <ul className="text-sm space-y-1 list-disc list-inside text-amber-800 dark:text-amber-200">
                                <li>Skills are inferred from completed courses and training history</li>
                                <li>Skill levels are categorized as Beginner, Intermediate, or Advanced</li>
                                <li>Gaps are identified when skills are below the expected level for a role</li>
                                <li>Recommendations are generated based on skill gaps and career goals</li>
                            </ul>
                        </div>
                    </div>
                </div>
            </section>

            {/* FAQ Section */}
            <section id="faq" className="bg-white dark:bg-slate-900 p-6 rounded-xl border border-slate-200 dark:border-slate-800">
                <h2 className="text-2xl font-semibold text-slate-900 dark:text-white mb-4 flex items-center gap-2">
                    <HelpCircle className="text-emerald-500" size={24} />
                    Frequently Asked Questions
                </h2>
                <div className="space-y-4">
                    <div className="p-4 bg-slate-50 dark:bg-slate-800 rounded-lg">
                        <h4 className="font-semibold text-slate-900 dark:text-white mb-2">How are skills assessed?</h4>
                        <p className="text-sm text-slate-600 dark:text-slate-400">
                            Skills are automatically inferred from your completed training courses and learning history. 
                            The system analyzes course titles, categories, and content to determine your proficiency level in various skill areas.
                        </p>
                    </div>
                    <div className="p-4 bg-slate-50 dark:bg-slate-800 rounded-lg">
                        <h4 className="font-semibold text-slate-900 dark:text-white mb-2">What is the "Swiss Cheese" profile?</h4>
                        <p className="text-sm text-slate-600 dark:text-slate-400">
                            The Swiss Cheese profile visualizes your skills, showing both strengths (solid areas) and gaps (holes). 
                            This helps identify areas where additional training would be most beneficial.
                        </p>
                    </div>
                    <div className="p-4 bg-slate-50 dark:bg-slate-800 rounded-lg">
                        <h4 className="font-semibold text-slate-900 dark:text-white mb-2">How do I access course content?</h4>
                        <p className="text-sm text-slate-600 dark:text-slate-400">
                            Click "Start" on any course card to begin learning. In production, this will open the actual course content 
                            (PDFs, videos, or interactive modules) from Škoda's Learning Management System.
                        </p>
                    </div>
                    <div className="p-4 bg-slate-50 dark:bg-slate-800 rounded-lg">
                        <h4 className="font-semibold text-slate-900 dark:text-white mb-2">Can I search for specific courses?</h4>
                        <p className="text-sm text-slate-600 dark:text-slate-400">
                            Yes! Use the search bar on the Daily Micro-Challenges page to search by course title, topic, category, or description.
                        </p>
                    </div>
                </div>
            </section>
        </div>
    );
}

