"use client";

import { Lock, User, Moon } from "lucide-react";
import { useThemeMode } from "@/components/theme-provider";

export default function SettingsPage() {
    const { theme, setTheme } = useThemeMode();

    return (
        <div className="max-w-4xl mx-auto space-y-8">
            <h1 className="text-3xl font-bold text-slate-900 dark:text-slate-100">Settings</h1>

            <div className="bg-white dark:bg-slate-950 rounded-xl border border-slate-200 dark:border-slate-800 overflow-hidden">
                {/* Profile Section */}
                <div className="p-6 border-b border-slate-200 dark:border-slate-800">
                    <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                        <User size={20} className="text-emerald-500" /> Profile Settings
                    </h2>
                    <div className="grid gap-4 max-w-md">
                        <div>
                            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Display Name</label>
                            <input type="text" defaultValue="Maria" className="w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-900" />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Role</label>
                            <div className="relative group">
                                <input
                                    type="text"
                                    defaultValue="HR Manager"
                                    disabled
                                    className="w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-slate-100 dark:bg-slate-800 text-slate-500 cursor-not-allowed"
                                />
                                <div className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 group-hover:text-slate-600 dark:group-hover:text-slate-300 transition-colors">
                                    <Lock size={16} />
                                </div>

                                {/* Tooltip */}
                                <div className="absolute bottom-full left-0 mb-1 inline-flex p-2 bg-slate-800 text-white text-xs rounded-lg shadow-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-10 max-w-xs">
                                    Only IT Team can modify user roles.
                                    <div className="absolute top-full left-4 -mt-1 border-4 border-transparent border-t-slate-800"></div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Appearance */}
                <div className="p-6">
                    <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                        <Moon size={20} className="text-purple-500" /> Appearance
                    </h2>
                    <div className="flex items-center gap-4">
                        <button
                            onClick={() => setTheme("light")}
                            className={`px-4 py-2 rounded-lg border transition-colors ${theme === 'light' ? 'bg-emerald-100 border-emerald-500 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400' : 'bg-slate-100 dark:bg-slate-800 border-slate-200 dark:border-slate-700 text-slate-900 dark:text-slate-100 hover:border-emerald-500'}`}
                        >
                            Light
                        </button>
                        <button
                            onClick={() => setTheme("dark")}
                            className={`px-4 py-2 rounded-lg border transition-colors ${theme === 'dark' ? 'bg-emerald-100 border-emerald-500 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400' : 'bg-slate-100 dark:bg-slate-800 border-slate-200 dark:border-slate-700 text-slate-900 dark:text-slate-100 hover:border-emerald-500'}`}
                        >
                            Dark
                        </button>
                        <button
                            onClick={() => setTheme("system")}
                            className={`px-4 py-2 rounded-lg border transition-colors ${theme === 'system' ? 'bg-emerald-100 border-emerald-500 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400' : 'bg-slate-100 dark:bg-slate-800 border-slate-200 dark:border-slate-700 text-slate-900 dark:text-slate-100 hover:border-emerald-500'}`}
                        >
                            System
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}
