"use client";

import { ThemeProvider } from "@/components/theme-provider";
import { AuthProvider } from "@/context/auth-context";

export function Providers({ children }: { children: React.ReactNode }) {
    return (
        <ThemeProvider>
            <AuthProvider>
                {children}
            </AuthProvider>
        </ThemeProvider>
    );
}
