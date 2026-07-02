"use client";

import * as React from "react";
import { GitFork } from "lucide-react";

interface Node {
  id: string;
  label: string;
  x: number;
  y: number;
  level: number;
  children?: string[];
}

export function MindMap() {
  const nodes: Node[] = [
    { id: "1", label: "Java Platform", x: 10, y: 110, level: 0, children: ["2", "3", "4"] },
    { id: "2", label: "Swing (GUI)", x: 105, y: 30, level: 1 },
    { id: "3", label: "JDBC DB API", x: 105, y: 110, level: 1, children: ["5", "6", "7"] },
    { id: "4", label: "Servlets (Web)", x: 105, y: 190, level: 1 },
    { id: "5", label: "Drivers", x: 200, y: 70, level: 2 },
    { id: "6", label: "Connection", x: 200, y: 110, level: 2 },
    { id: "7", label: "ResultSet", x: 200, y: 150, level: 2 },
  ];

  const connections = [
    { from: "1", to: "2" },
    { from: "1", to: "3" },
    { from: "1", to: "4" },
    { from: "3", to: "5" },
    { from: "3", to: "6" },
    { from: "3", to: "7" },
  ];

  const [activeNode, setActiveNode] = React.useState<string | null>("3");

  return (
    <div className="rounded-xl border border-border/40 bg-black/30 p-3 space-y-3 flex flex-col h-[340px]">
      <div className="flex items-center gap-1.5 text-xs font-semibold text-white shrink-0">
        <GitFork className="h-4 w-4 text-indigo-400" />
        Interactive AI Mind Map
      </div>

      <div className="flex-1 relative border border-border/10 rounded-lg bg-black/40 overflow-hidden select-none min-h-0">
        <svg className="absolute inset-0 w-full h-full pointer-events-none">
          {connections.map((conn, idx) => {
            const fromNode = nodes.find(n => n.id === conn.from);
            const toNode = nodes.find(n => n.id === conn.to);
            if (!fromNode || !toNode) return null;
            // Draw a bezier curve
            const startX = fromNode.x + 80;
            const startY = fromNode.y + 15;
            const endX = toNode.x;
            const endY = toNode.y + 15;
            const controlX = startX + 20;
            const path = `M ${startX} ${startY} C ${controlX} ${startY}, ${controlX} ${endY}, ${endX} ${endY}`;
            return (
              <path
                key={idx}
                d={path}
                fill="none"
                stroke={activeNode === conn.from || activeNode === conn.to ? "#6366f1" : "#374151"}
                strokeWidth="1.5"
                className="transition-all duration-300"
              />
            );
          })}
        </svg>

        {nodes.map((node) => {
          const isActive = activeNode === node.id;
          return (
            <button
              key={node.id}
              onClick={() => setActiveNode(node.id)}
              style={{ left: `${node.x}px`, top: `${node.y}px` }}
              className={`absolute w-[80px] h-[30px] rounded-md text-[9px] font-semibold flex items-center justify-center border transition-all duration-300 ${
                isActive
                  ? "bg-indigo-600/35 border-indigo-500 text-white shadow-[0_0_8px_rgba(99,102,241,0.4)]"
                  : "bg-neutral-900/90 border-border/30 text-muted-foreground hover:text-white hover:border-neutral-500"
              }`}
            >
              <span className="truncate px-1">{node.label}</span>
            </button>
          );
        })}
      </div>

      <div className="text-[10px] text-muted-foreground leading-normal bg-white/5 p-2 rounded-lg shrink-0">
        {activeNode === "3" && "JDBC (Java Database Connectivity) allows Java applications to interact with database engines using SQL."}
        {activeNode === "1" && "Java Platform contains tools, runtimes, and APIs for building cross-platform applications."}
        {activeNode === "2" && "Swing is a lightweight GUI widget toolkit for Java providing cross-platform windows."}
        {activeNode === "4" && "Servlets are Java classes that handle HTTP requests and generate dynamic web content."}
        {activeNode === "5" && "Drivers implement the JDBC interfaces for a specific database vendor (e.g. MySQL, SQLite)."}
        {activeNode === "6" && "Connection represents a session/socket channel established with the database server."}
        {activeNode === "7" && "ResultSet stores query responses and lets applications iterate over database rows."}
      </div>
    </div>
  );
}
