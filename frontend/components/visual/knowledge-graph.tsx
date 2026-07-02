"use client";

import * as React from "react";
import { Network } from "lucide-react";

interface Node {
  id: string;
  label: string;
  x: number;
  y: number;
}

export function KnowledgeGraph() {
  const [nodes, setNodes] = React.useState<Node[]>([
    { id: "java", label: "Java", x: 110, y: 110 },
    { id: "swing", label: "Swing", x: 30, y: 50 },
    { id: "awt", label: "AWT", x: 40, y: 170 },
    { id: "jdbc", label: "JDBC", x: 190, y: 50 },
    { id: "servlets", label: "Servlets", x: 200, y: 170 },
  ]);

  const links = [
    { source: "java", target: "swing" },
    { source: "java", target: "awt" },
    { source: "java", target: "jdbc" },
    { source: "java", target: "servlets" },
    { source: "swing", target: "awt" },
    { source: "jdbc", target: "servlets" },
  ];

  const [draggedNodeId, setDraggedNodeId] = React.useState<string | null>(null);
  const containerRef = React.useRef<HTMLDivElement>(null);

  const handleMouseDown = (id: string, e: React.MouseEvent) => {
    e.preventDefault();
    setDraggedNodeId(id);
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!draggedNodeId || !containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left - 30; // center offset
    const y = e.clientY - rect.top - 15;
    
    // Clamp to viewport
    const clampedX = Math.max(10, Math.min(rect.width - 70, x));
    const clampedY = Math.max(10, Math.min(rect.height - 40, y));

    setNodes((prev) =>
      prev.map((n) => (n.id === draggedNodeId ? { ...n, x: clampedX, y: clampedY } : n))
    );
  };

  const handleMouseUpOrLeave = () => {
    setDraggedNodeId(null);
  };

  return (
    <div className="rounded-xl border border-border/40 bg-black/30 p-3 space-y-3 flex flex-col h-[340px]">
      <div className="flex items-center justify-between shrink-0">
        <div className="flex items-center gap-1.5 text-xs font-semibold text-white">
          <Network className="h-4 w-4 text-indigo-400" />
          Obsidian Knowledge Graph
        </div>
        <span className="text-[9px] text-muted-foreground bg-white/5 px-2 py-0.5 rounded-full">Drag Nodes</span>
      </div>

      <div
        ref={containerRef}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUpOrLeave}
        onMouseLeave={handleMouseUpOrLeave}
        className="flex-1 relative border border-border/10 rounded-lg bg-black/40 overflow-hidden select-none min-h-0"
      >
        <svg className="absolute inset-0 w-full h-full pointer-events-none">
          {links.map((link, idx) => {
            const sourceNode = nodes.find((n) => n.id === link.source);
            const targetNode = nodes.find((n) => n.id === link.target);
            if (!sourceNode || !targetNode) return null;

            return (
              <line
                key={idx}
                x1={sourceNode.x + 30}
                y1={sourceNode.y + 15}
                x2={targetNode.x + 30}
                y2={targetNode.y + 15}
                stroke={draggedNodeId === link.source || draggedNodeId === link.target ? "#818cf8" : "#27272a"}
                strokeWidth="1.5"
                className="transition-all duration-75"
              />
            );
          })}
        </svg>

        {nodes.map((node) => {
          const isDragging = draggedNodeId === node.id;
          return (
            <div
              key={node.id}
              onMouseDown={(e) => handleMouseDown(node.id, e)}
              style={{
                left: `${node.x}px`,
                top: `${node.y}px`,
                cursor: isDragging ? "grabbing" : "grab",
              }}
              className={`absolute w-[60px] h-[30px] rounded-full text-[9px] font-semibold flex items-center justify-center border transition-shadow duration-200 select-none ${
                isDragging
                  ? "bg-indigo-600 border-indigo-400 text-white shadow-[0_0_12px_rgba(99,102,241,0.6)]"
                  : "bg-neutral-900 border-border/40 text-white/90 hover:border-indigo-400 hover:text-white"
              }`}
            >
              {node.label}
            </div>
          );
        })}
      </div>
    </div>
  );
}
