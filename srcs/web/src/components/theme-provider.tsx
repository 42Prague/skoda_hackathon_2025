"use client";

import {
    createContext,
    useContext,
    useEffect,
    useMemo,
    useState,
    useTransition,
    type ReactNode,
} from "react";

type ThemeSetting = "light" | "dark" | "system";
type ResolvedTheme = "light" | "dark";

interface ThemeContextValue {
    theme: ThemeSetting;
    resolvedTheme: ResolvedTheme;
    setTheme: (theme: ThemeSetting) => void;
}

const STORAGE_KEY = "s3-theme";

const ThemeContext = createContext<ThemeContextValue | undefined>(undefined);

export function ThemeProvider({ children }: { children: ReactNode }) {
    const [theme, setTheme] = useState<ThemeSetting>("system");
    const [resolvedTheme, setResolvedTheme] = useState<ResolvedTheme>("light");
    const [, startTransition] = useTransition();

    useEffect(() => {
        if (typeof window === "undefined") {
            return;
        }
        const stored = localStorage.getItem(STORAGE_KEY) as ThemeSetting | null;
        if (stored === "light" || stored === "dark" || stored === "system") {
            startTransition(() => setTheme(stored));
        }
    }, [startTransition]);

    useEffect(() => {
        if (typeof window === "undefined") {
            return;
        }

        const media = window.matchMedia("(prefers-color-scheme: dark)");

        const resolveTheme = (value: ThemeSetting): ResolvedTheme => {
            if (value === "system") {
                return media.matches ? "dark" : "light";
            }
            return value;
        };

        const applyTheme = (value: ThemeSetting) => {
            const resolved = resolveTheme(value);
            setResolvedTheme(resolved);

            const targets = [document.documentElement, document.body].filter(
                (el): el is HTMLElement => Boolean(el),
            );
            targets.forEach((el) => {
                el.classList.remove("light", "dark");
                el.classList.add(resolved);
            });

            document.documentElement.dataset.theme = resolved;
            localStorage.setItem(STORAGE_KEY, value);
        };

        applyTheme(theme);

        const handleChange = () => {
            if (theme === "system") {
                applyTheme("system");
            }
        };

        media.addEventListener("change", handleChange);
        return () => media.removeEventListener("change", handleChange);
    }, [theme]);

    const value = useMemo(
        () => ({
            theme,
            resolvedTheme,
            setTheme,
        }),
        [theme, resolvedTheme],
    );

    return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

export function useThemeMode() {
    const ctx = useContext(ThemeContext);
    if (!ctx) {
        throw new Error("useThemeMode must be used within ThemeProvider");
    }
    return ctx;
}
