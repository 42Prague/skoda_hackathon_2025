import type { Metadata } from "next";
import "./globals.css";
import { Providers } from "@/components/providers";
import { AppShell } from "@/components/app-shell";

import { Toaster } from "sonner";

export const metadata: Metadata = {
  title: "Skoda HR Dashboard",
  description: "HR Analytics and Skill Management",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body
        className="antialiased bg-slate-50 dark:bg-slate-950"
      >
        <Providers>
          <AppShell>
            {children}
          </AppShell>
          <Toaster position="top-center" richColors />
        </Providers>
      </body>
    </html>
  );
}
