import type { Metadata } from "next";
import { Manrope, Geist } from "next/font/google";

import { AppProviders } from "@/components/providers/app-providers";
import "@/app/globals.css";
import { cn } from "@/lib/utils";

const geist = Geist({subsets:['latin'],variable:'--font-sans'});

const manrope = Manrope({
  subsets: ["latin"]
});

export const metadata: Metadata = {
  title: "AI Knowledge Assistant",
  description: "Full-stack knowledge assistant starter built with Next.js and FastAPI."
};

import { ErrorBoundary } from "@/components/ErrorBoundary";

export default function RootLayout({
  children
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning className={cn("font-sans", geist.variable)}>
      <body className={manrope.className}>
        <ErrorBoundary>
          <AppProviders>{children}</AppProviders>
        </ErrorBoundary>
      </body>
    </html>
  );
}
