"use client";

import * as React from "react";

export function useAutoScroll<T extends HTMLElement>(dependency: unknown) {
  const ref = React.useRef<T | null>(null);

  React.useEffect(() => {
    if (!ref.current) {
      return;
    }

    ref.current.scrollTo({
      top: ref.current.scrollHeight,
      behavior: "smooth"
    });
  }, [dependency]);

  return ref;
}
