"use client";

import { useMemo, useState } from "react";
import { useAuth } from "@/context/auth-context";
import { Lock, User, ArrowRight, HelpCircle } from "lucide-react";

const REQUIRED_USERNAME = process.env.NEXT_PUBLIC_LOGIN_USERNAME || "";
const REQUIRED_PASSWORD = process.env.NEXT_PUBLIC_LOGIN_PASSWORD || "";

export default function LoginPage() {
    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [errorMessage, setErrorMessage] = useState("");
    const { login } = useAuth();
    const isLoginConfigured = useMemo(
        () => Boolean(REQUIRED_USERNAME && REQUIRED_PASSWORD),
        []
    );

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (!username || !password || isSubmitting) {
            return;
        }

        if (!isLoginConfigured) {
            setErrorMessage("Login is temporarily unavailable. Please contact the administrator.");
            return;
        }

        if (username !== REQUIRED_USERNAME || password !== REQUIRED_PASSWORD) {
            setErrorMessage("Invalid username or password.");
            return;
        }

        setErrorMessage("");
        setIsSubmitting(true);
        login(username);
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 via-white to-slate-100 dark:from-slate-900 dark:via-slate-950 dark:to-slate-900 p-4">
            <div className="w-full max-w-md bg-white dark:bg-slate-950 rounded-2xl shadow-2xl border border-slate-200 dark:border-slate-800 overflow-hidden transform transition-all duration-500 ease-out animate-fade-in-up">
                <div className="p-8">
                    <div className="text-center mb-8">
                        <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-gradient-to-br from-emerald-100 to-emerald-200 dark:from-emerald-900/30 dark:to-emerald-800/30 text-emerald-600 dark:text-emerald-400 mb-4 shadow-lg transform transition-transform duration-300 hover:scale-110">
                            <Lock size={32} />
                        </div>
                        <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">Welcome Back</h1>
                        <p className="text-slate-500 dark:text-slate-400 mt-2">Sign in to access the HR Dashboard</p>
                    </div>

                    <form onSubmit={handleSubmit} className="space-y-6">
                        <div className="space-y-2">
                            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2 transition-colors">
                                Username
                            </label>
                            <div className="relative group">
                                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400 transition-colors group-focus-within:text-emerald-500">
                                    <User size={20} className="transition-transform duration-200 group-focus-within:scale-110" />
                                </div>
                                <input
                                    type="text"
                                    value={username}
                                    onChange={(e) => setUsername(e.target.value)}
                                    className="block w-full pl-10 pr-3 py-3 border border-slate-300 dark:border-slate-700 rounded-xl bg-slate-50 dark:bg-slate-900 text-slate-900 dark:text-slate-100 placeholder:text-slate-400 dark:placeholder:text-slate-500 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 focus:bg-white dark:focus:bg-slate-900 transition-all duration-200 ease-out hover:border-slate-400 dark:hover:border-slate-600"
                                    placeholder="Enter your username"
                                    required
                                    disabled={isSubmitting}
                                />
                            </div>
                        </div>

                        <div className="space-y-2">
                            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2 transition-colors">
                                Password
                            </label>
                            <div className="relative group">
                                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400 transition-colors group-focus-within:text-emerald-500">
                                    <Lock size={20} className="transition-transform duration-200 group-focus-within:scale-110" />
                                </div>
                                <input
                                    type="password"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    className="block w-full pl-10 pr-3 py-3 border border-slate-300 dark:border-slate-700 rounded-xl bg-slate-50 dark:bg-slate-900 text-slate-900 dark:text-slate-100 placeholder:text-slate-400 dark:placeholder:text-slate-500 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 focus:bg-white dark:focus:bg-slate-900 transition-all duration-200 ease-out hover:border-slate-400 dark:hover:border-slate-600"
                                    placeholder="••••••••"
                                    required
                                    disabled={isSubmitting}
                                />
                            </div>
                        </div>

                        {errorMessage && (
                            <div className="p-3 rounded-xl bg-red-50 border border-red-200 text-red-700 text-sm flex items-center gap-2 animate-fade-in-up">
                                <Lock size={16} />
                                <span>{errorMessage}</span>
                            </div>
                        )}

                        <button
                            type="submit"
                            disabled={isSubmitting}
                            className="w-full flex items-center justify-center gap-2 py-3 px-4 bg-gradient-to-r from-emerald-600 to-emerald-700 hover:from-emerald-700 hover:to-emerald-800 text-white font-medium rounded-xl transition-all duration-200 ease-out focus:ring-2 focus:ring-emerald-500 focus:ring-offset-2 dark:focus:ring-offset-slate-900 transform hover:scale-[1.02] active:scale-[0.98] shadow-lg hover:shadow-xl disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
                        >
                            {isSubmitting ? (
                                <>
                                    <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                                    <span>Signing in...</span>
                                </>
                            ) : (
                                <>
                                    Sign In <ArrowRight size={20} className="transition-transform duration-200 group-hover:translate-x-1" />
                                </>
                            )}
                        </button>
                    </form>

                    <div className="mt-6 space-y-3">
                        <div className="flex items-start gap-2 p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
                            <HelpCircle className="text-blue-600 dark:text-blue-400 mt-0.5 flex-shrink-0" size={16} />
                            <p className="text-xs text-blue-800 dark:text-blue-200 leading-relaxed">
                                Forgot your password? Please contact the IT Support team for assistance with account recovery.
                            </p>
                        </div>
                    </div>
                </div>

                <div className="bg-gradient-to-r from-slate-50 to-slate-100 dark:from-slate-900/50 dark:to-slate-800/50 p-4 text-center border-t border-slate-200 dark:border-slate-800">
                    <p className="text-xs text-slate-500 dark:text-slate-400 flex items-center justify-center gap-1">
                        <Lock size={12} className="text-emerald-500" />
                        Protected by S³ Enterprise Security
                    </p>
                </div>
            </div>
        </div>
    );
}
