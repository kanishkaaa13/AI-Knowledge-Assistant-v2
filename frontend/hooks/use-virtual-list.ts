"use client";

import * as React from "react";

export function useVirtualList<T>({
  items,
  itemHeight,
  overscan = 4
}: {
  items: T[];
  itemHeight: number;
  overscan?: number;
}) {
  const containerRef = React.useRef<HTMLDivElement | null>(null);
  const [scrollTop, setScrollTop] = React.useState(0);
  const [viewportHeight, setViewportHeight] = React.useState(640);

  React.useEffect(() => {
    const container = containerRef.current;
    if (!container) {
      return;
    }

    const handleScroll = () => setScrollTop(container.scrollTop);
    const handleResize = () => setViewportHeight(container.clientHeight);

    handleResize();
    container.addEventListener("scroll", handleScroll);
    window.addEventListener("resize", handleResize);
    return () => {
      container.removeEventListener("scroll", handleScroll);
      window.removeEventListener("resize", handleResize);
    };
  }, []);

  const startIndex = Math.max(0, Math.floor(scrollTop / itemHeight) - overscan);
  const visibleCount = Math.ceil(viewportHeight / itemHeight) + overscan * 2;
  const endIndex = Math.min(items.length, startIndex + visibleCount);

  return {
    containerRef,
    totalHeight: items.length * itemHeight,
    offsetY: startIndex * itemHeight,
    visibleItems: items.slice(startIndex, endIndex)
  };
}
