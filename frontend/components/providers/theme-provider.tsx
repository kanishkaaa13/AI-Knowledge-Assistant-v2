"use client";

import * as React from "react";
import { ThemeProvider as NextThemesProvider } from "next-themes";

export function ThemeProvider({
  children
}: {
  children: React.ReactNode;
}) {
  return (
    <NextThemesProvider attribute="class" defaultTheme="dark" enableSystem={false} themes={["light", "dark", "oled", "purple", "blue"]}>
      {children}
    </NextThemesProvider>
  );
}
