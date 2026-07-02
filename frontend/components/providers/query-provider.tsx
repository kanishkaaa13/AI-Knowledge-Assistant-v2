"use client";

import * as React from "react";
import {
  QueryClientProvider,
  QueryClientProviderProps
} from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";

import { createQueryClient } from "@/lib/query-client";

export function QueryProvider({
  children
}: Pick<QueryClientProviderProps, "children">) {
  const [client] = React.useState(() => createQueryClient());

  return (
    <QueryClientProvider client={client}>
      {children}
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  );
}
