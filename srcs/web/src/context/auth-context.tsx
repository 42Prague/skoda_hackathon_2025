"use client";

import React, { createContext, useContext, useState, useEffect, useTransition } from "react";
import { useRouter, usePathname } from "next/navigation";

interface User {
    name: string;
    role: string;
    email: string;
}

interface AuthContextType {
    user: User | null;
    login: (username: string) => void;
    logout: () => void;
    isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
    const [user, setUser] = useState<User | null>(null);
    const [, startTransition] = useTransition();
    const router = useRouter();
    const pathname = usePathname();

    const [isLoading, setIsLoading] = useState(false);
    const [isLoggingOut, setIsLoggingOut] = useState(false);

    useEffect(() => {
        if (typeof window === "undefined") {
            return;
        }
        const storedUser = localStorage.getItem("s3_user");
        if (storedUser) {
            startTransition(() => setUser(JSON.parse(storedUser)));
        }
    }, [startTransition]);

    const login = (username: string) => {
        setIsLoggingOut(false);
        setIsLoading(true);
        // Simulate network delay for transition
        setTimeout(() => {
            const mockUser: User = {
                name: "Maria",
                role: "HR Manager",
                email: `${username}@skoda-auto.cz`
            };
            setUser(mockUser);
            localStorage.setItem("s3_user", JSON.stringify(mockUser));
            setIsLoading(false);
            router.push("/");
        }, 1500);
    };

    const logout = () => {
        setIsLoggingOut(true);
        setIsLoading(true);
        setTimeout(() => {
            setUser(null);
            localStorage.removeItem("s3_user");
            setIsLoading(false);
            setIsLoggingOut(false);
            router.push("/login");
        }, 1000);
    };

    // Protect routes
    useEffect(() => {
        const isLoginPage = pathname === "/login";
        const storedUser = localStorage.getItem("s3_user");

        if (!storedUser && !isLoginPage) {
            router.push("/login");
        } else if (storedUser && isLoginPage) {
            router.push("/");
        }
    }, [pathname, router]);

    return (
        <AuthContext.Provider value={{ user, login, logout, isAuthenticated: !!user }}>
            {isLoading && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-white/90 dark:bg-slate-950/90 backdrop-blur-md transition-all duration-300 ease-out">
                    <div className="flex flex-col items-center gap-4 p-8 bg-white dark:bg-slate-900 rounded-2xl shadow-2xl border border-slate-200 dark:border-slate-800 transform transition-all duration-300 animate-scale-in">
                        <div className="w-12 h-12 border-4 border-emerald-500 border-t-transparent rounded-full animate-spin"></div>
                        <p className="text-emerald-600 dark:text-emerald-400 font-medium text-sm animate-pulse">
                            {isLoggingOut ? "Signing out..." : "Signing in..."}
                        </p>
                    </div>
                </div>
            )}
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth() {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error("useAuth must be used within an AuthProvider");
    }
    return context;
}
