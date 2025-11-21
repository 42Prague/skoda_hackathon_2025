"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { LayoutDashboard, Users, BookOpen, Settings, LogOut, User, Lock, Building2, BarChart3, Search, Menu, X } from "lucide-react";
import { useAuth } from "@/context/auth-context";

export function AppShell({ children }: { children: React.ReactNode }) {
    const pathname = usePathname();
    const { user, logout } = useAuth();
    const isLoginPage = pathname === "/login";
    const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

    if (isLoginPage) {
        return <>{children}</>;
    }

    return (
        <div className="flex h-screen">
            {/* Sidebar */}
            <aside className="w-64 bg-white dark:bg-slate-950 border-r border-slate-200 dark:border-slate-800 hidden md:flex flex-col">
                <div className="p-6 border-b border-slate-200 dark:border-slate-800">
                    <h1 className="text-2xl font-bold text-emerald-600 dark:text-emerald-500">S³</h1>
                    <p className="text-xs text-slate-500 dark:text-slate-400">Skoda Smart Stream</p>
                </div>

                <nav className="flex-1 p-4 space-y-2">
                    <Link href="/" className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-colors ${pathname === '/' ? 'bg-emerald-50 dark:bg-emerald-900/20 text-emerald-600 dark:text-emerald-400' : 'text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800'}`}>
                        <Search size={20} />
                        <span className="font-medium">Employee Search</span>
                    </Link>
                    <Link href="/department" className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-colors ${pathname === '/department' ? 'bg-emerald-50 dark:bg-emerald-900/20 text-emerald-600 dark:text-emerald-400' : 'text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800'}`}>
                        <LayoutDashboard size={20} />
                        <span className="font-medium">Department Overview</span>
                    </Link>
                    <Link
                        href="/analytics"
                        className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all ${pathname === "/analytics"
                            ? "bg-emerald-50 text-emerald-700 dark:bg-emerald-900/20 dark:text-emerald-400 font-medium"
                            : "text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-900"
                            }`}
                    >
                        <BarChart3 size={20} />
                        Analytics
                    </Link>
                    <Link
                        href="/documentation"
                        className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-colors ${pathname === '/documentation' ? 'bg-emerald-50 dark:bg-emerald-900/20 text-emerald-600 dark:text-emerald-400' : 'text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800'}`}>
                        <BookOpen size={20} />
                        <span className="font-medium">Documentation</span>
                    </Link>
                </nav>

                <div className="p-4 border-t border-slate-200 dark:border-slate-800">
                    <div className="group relative">
                        <div className="flex items-center gap-3 p-3 rounded-xl bg-gradient-to-r from-slate-50 to-white dark:from-slate-900 dark:to-slate-950 hover:from-emerald-50 hover:to-emerald-50/50 dark:hover:from-emerald-900/20 dark:hover:to-emerald-900/10 transition-all duration-300 cursor-pointer border border-slate-200 dark:border-slate-800 hover:border-emerald-300 dark:hover:border-emerald-700/50 shadow-sm hover:shadow-md group-hover:scale-[1.02]">
                            {/* Avatar with ring */}
                            <div className="relative">
                                <div className="w-11 h-11 rounded-full bg-gradient-to-br from-emerald-500 via-emerald-600 to-emerald-700 dark:from-emerald-600 dark:via-emerald-700 dark:to-emerald-800 flex items-center justify-center text-white shadow-lg group-hover:shadow-xl group-hover:ring-2 group-hover:ring-emerald-400/50 dark:group-hover:ring-emerald-500/50 transition-all duration-300 group-hover:scale-110">
                                    <User size={20} className="drop-shadow-sm" />
                                </div>
                                <div className="absolute -bottom-0.5 -right-0.5 w-3.5 h-3.5 bg-emerald-500 dark:bg-emerald-400 rounded-full border-2 border-white dark:border-slate-950 shadow-sm"></div>
                            </div>
                            
                            {/* User info */}
                            <div className="flex-1 min-w-0">
                                <p className="text-sm font-bold text-slate-900 dark:text-slate-100 truncate group-hover:text-emerald-700 dark:group-hover:text-emerald-400 transition-colors">
                                    {user?.name || 'User'}
                                </p>
                                <p className="text-xs text-slate-500 dark:text-slate-400 truncate mt-0.5 font-medium">
                                    {user?.role || 'Employee'}
                                </p>
                            </div>
                            
                            {/* Dropdown icon with animation */}
                            <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-slate-100 dark:bg-slate-800 group-hover:bg-emerald-100 dark:group-hover:bg-emerald-900/30 transition-all duration-300">
                                <svg width="14" height="14" viewBox="0 0 14 14" fill="none" className="text-slate-500 dark:text-slate-400 group-hover:text-emerald-600 dark:group-hover:text-emerald-400 transform group-hover:rotate-180 transition-all duration-300">
                                    <path d="M3.5 5.25L7 8.75L10.5 5.25" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                                </svg>
                            </div>
                        </div>

                        {/* Premium Popover Design */}
                        <div className="absolute bottom-full left-0 w-full mb-3 bg-white dark:bg-slate-950 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-2xl opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-300 ease-out transform translate-y-3 group-hover:translate-y-0 overflow-hidden z-50">
                            {/* Arrow pointer with shadow */}
                            <div className="absolute bottom-0 left-6 transform translate-y-1/2 rotate-45">
                                <div className="w-4 h-4 bg-white dark:bg-slate-950 border-r border-b border-slate-200 dark:border-slate-800 shadow-lg"></div>
                            </div>
                            
                            <div className="relative bg-white dark:bg-slate-950 rounded-2xl overflow-hidden">
                                {/* User info header with gradient */}
                                <div className="px-5 py-4 bg-gradient-to-br from-slate-50 via-white to-slate-50 dark:from-slate-900 dark:via-slate-950 dark:to-slate-900 border-b border-slate-200 dark:border-slate-800">
                                    <div className="flex items-center gap-3 mb-2">
                                        <div className="w-12 h-12 rounded-full bg-gradient-to-br from-emerald-500 to-emerald-600 dark:from-emerald-600 dark:to-emerald-700 flex items-center justify-center text-white shadow-lg">
                                            <User size={20} />
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <p className="text-sm font-bold text-slate-900 dark:text-slate-100 truncate">{user?.name || 'User'}</p>
                                            <p className="text-xs text-slate-500 dark:text-slate-400 truncate mt-0.5">{user?.email || user?.role || 'Employee'}</p>
                                        </div>
                                    </div>
                                </div>

                                {/* Menu items with better spacing */}
                                <div className="py-2">
                                    <Link
                                        href="/settings"
                                        className={`w-full text-left px-5 py-3.5 text-sm flex items-center gap-3 transition-all duration-200 group/item ${
                                            pathname === '/settings' 
                                                ? 'bg-emerald-50 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-400 font-semibold border-l-4 border-emerald-500' 
                                                : 'text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-900/50 border-l-4 border-transparent'
                                        }`}
                                    >
                                        <div className={`p-1.5 rounded-lg ${
                                            pathname === '/settings' 
                                                ? 'bg-emerald-100 dark:bg-emerald-900/50' 
                                                : 'bg-slate-100 dark:bg-slate-800 group-hover/item:bg-emerald-50 dark:group-hover/item:bg-emerald-900/20'
                                        } transition-colors`}>
                                            <Settings size={16} className={pathname === '/settings' ? 'text-emerald-600 dark:text-emerald-400' : 'text-slate-600 dark:text-slate-400'} />
                                        </div>
                                        <span className="flex-1">Settings</span>
                                        {pathname === '/settings' && (
                                            <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></div>
                                        )}
                                    </Link>
                                    
                                    <div className="my-1 mx-5 border-t border-slate-200 dark:border-slate-800"></div>
                                    
                                    <button
                                        onClick={logout}
                                        className="w-full text-left px-5 py-3.5 text-sm text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 flex items-center gap-3 transition-all duration-200 group/logout border-l-4 border-transparent hover:border-red-500"
                                    >
                                        <div className="p-1.5 rounded-lg bg-red-50 dark:bg-red-900/20 group-hover/logout:bg-red-100 dark:group-hover/logout:bg-red-900/30 transition-colors">
                                            <LogOut size={16} className="text-red-600 dark:text-red-400 group-hover/logout:rotate-12 transition-transform duration-200" />
                                        </div>
                                        <span className="flex-1 font-semibold">Log Out</span>
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </aside>

            {/* Mobile Menu Overlay */}
            {mobileMenuOpen && (
                <div 
                    className="fixed inset-0 bg-black/50 z-40 md:hidden"
                    onClick={() => setMobileMenuOpen(false)}
                />
            )}

            {/* Mobile Sidebar */}
            <aside className={`fixed inset-y-0 left-0 w-64 bg-white dark:bg-slate-950 border-r border-slate-200 dark:border-slate-800 z-50 transform transition-transform duration-300 ease-in-out md:hidden flex flex-col ${
                mobileMenuOpen ? 'translate-x-0' : '-translate-x-full'
            }`}>
                <div className="p-6 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
                    <div>
                        <h1 className="text-2xl font-bold text-emerald-600 dark:text-emerald-500">S³</h1>
                        <p className="text-xs text-slate-500 dark:text-slate-400">Skoda Smart Stream</p>
                    </div>
                    <button
                        onClick={() => setMobileMenuOpen(false)}
                        className="p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                    >
                        <X size={24} className="text-slate-600 dark:text-slate-400" />
                    </button>
                </div>

                <nav className="flex-1 p-4 space-y-2 overflow-y-auto">
                    <Link 
                        href="/" 
                        onClick={() => setMobileMenuOpen(false)}
                        className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-colors ${pathname === '/' ? 'bg-emerald-50 dark:bg-emerald-900/20 text-emerald-600 dark:text-emerald-400' : 'text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800'}`}
                    >
                        <Search size={20} />
                        <span className="font-medium">Employee Search</span>
                    </Link>
                    <Link 
                        href="/department" 
                        onClick={() => setMobileMenuOpen(false)}
                        className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-colors ${pathname === '/department' ? 'bg-emerald-50 dark:bg-emerald-900/20 text-emerald-600 dark:text-emerald-400' : 'text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800'}`}
                    >
                        <LayoutDashboard size={20} />
                        <span className="font-medium">Department Overview</span>
                    </Link>
                    <Link
                        href="/analytics"
                        onClick={() => setMobileMenuOpen(false)}
                        className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all ${pathname === "/analytics"
                            ? "bg-emerald-50 text-emerald-700 dark:bg-emerald-900/20 dark:text-emerald-400 font-medium"
                            : "text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-900"
                            }`}
                    >
                        <BarChart3 size={20} />
                        <span className="font-medium">Analytics</span>
                    </Link>
                    <Link
                        href="/documentation"
                        onClick={() => setMobileMenuOpen(false)}
                        className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-colors ${pathname === '/documentation' ? 'bg-emerald-50 dark:bg-emerald-900/20 text-emerald-600 dark:text-emerald-400' : 'text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800'}`}
                    >
                        <BookOpen size={20} />
                        <span className="font-medium">Documentation</span>
                    </Link>
                </nav>

                <div className="p-4 border-t border-slate-200 dark:border-slate-800">
                    <div className="group relative">
                        <div className="flex items-center gap-3 p-3 rounded-xl bg-gradient-to-r from-slate-50 to-white dark:from-slate-900 dark:to-slate-950 hover:from-emerald-50 hover:to-emerald-50/50 dark:hover:from-emerald-900/20 dark:hover:to-emerald-900/10 transition-all duration-300 cursor-pointer border border-slate-200 dark:border-slate-800 hover:border-emerald-300 dark:hover:border-emerald-700/50 shadow-sm hover:shadow-md">
                            <div className="relative">
                                <div className="w-11 h-11 rounded-full bg-gradient-to-br from-emerald-500 via-emerald-600 to-emerald-700 dark:from-emerald-600 dark:via-emerald-700 dark:to-emerald-800 flex items-center justify-center text-white shadow-lg">
                                    <User size={20} className="drop-shadow-sm" />
                                </div>
                                <div className="absolute -bottom-0.5 -right-0.5 w-3.5 h-3.5 bg-emerald-500 dark:bg-emerald-400 rounded-full border-2 border-white dark:border-slate-950 shadow-sm"></div>
                            </div>
                            <div className="flex-1 min-w-0">
                                <p className="text-sm font-bold text-slate-900 dark:text-slate-100 truncate">
                                    {user?.name || 'User'}
                                </p>
                                <p className="text-xs text-slate-500 dark:text-slate-400 truncate mt-0.5 font-medium">
                                    {user?.role || 'Employee'}
                                </p>
                            </div>
                        </div>

                        <div className="mt-2 space-y-1">
                            <Link
                                href="/settings"
                                onClick={() => setMobileMenuOpen(false)}
                                className={`w-full text-left px-4 py-3 text-sm flex items-center gap-3 transition-all duration-200 rounded-lg ${
                                    pathname === '/settings' 
                                        ? 'bg-emerald-50 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-400 font-semibold' 
                                        : 'text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-900/50'
                                }`}
                            >
                                <Settings size={18} />
                                <span>Settings</span>
                            </Link>
                            
                            <button
                                onClick={() => {
                                    setMobileMenuOpen(false);
                                    logout();
                                }}
                                className="w-full text-left px-4 py-3 text-sm text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 flex items-center gap-3 transition-all duration-200 rounded-lg"
                            >
                                <LogOut size={18} />
                                <span className="font-semibold">Log Out</span>
                            </button>
                        </div>
                    </div>
                </div>
            </aside>

            {/* Main Content */}
            <main className="flex-1 flex flex-col overflow-hidden">
                <header className="h-16 bg-white dark:bg-slate-950 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between px-4 md:px-6">
                    <div className="flex items-center gap-4">
                        <button
                            onClick={() => setMobileMenuOpen(true)}
                            className="p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors md:hidden"
                        >
                            <Menu size={24} className="text-slate-600 dark:text-slate-400" />
                        </button>
                        <h2 className="text-lg font-semibold text-slate-800 dark:text-slate-100">
                            {pathname === '/' ? 'Employee Search' :
                                pathname === '/department' ? 'Department Overview' :
                                    pathname === '/feed' ? 'Daily Micro-Challenges' :
                                        pathname === '/documentation' ? 'Documentation' :
                                            pathname === '/settings' ? 'Settings' : 'Dashboard'}
                        </h2>
                    </div>
                    <div className="flex items-center gap-4">
                        <Link href="/feed" className="px-4 py-2 text-sm font-medium text-white bg-emerald-600 rounded-md hover:bg-emerald-700 transition-colors">
                            Daily Micro-Challenge
                        </Link>
                    </div>
                </header>
                <div className="flex-1 overflow-auto p-6">
                    {children}
                </div>
            </main>
        </div>
    );
}
