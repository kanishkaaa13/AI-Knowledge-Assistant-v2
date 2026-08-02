"use client";

import * as React from "react";
import { streamAssistantChat, StreamPayload } from "@/lib/chat-stream";
import type { RetrievedChunk } from "@/types/rag";

interface PipelineStep {
  id: string;
  label: string;
  status: "pending" | "active" | "completed";
}

interface SimulatorState {
  query: string;
  topK: number;
  isRunning: boolean;
  currentStep: number;
  steps: PipelineStep[];
  retrievedChunks: RetrievedChunk[];
  answer: string;
  sources: string[];
  vectorDim: number;
}

const INITIAL_STEPS: PipelineStep[] = [
  { id: "query", label: "Query Received", status: "pending" },
  { id: "embedding", label: "Embedding Model", status: "pending" },
  { id: "search", label: "Vector DB Search", status: "pending" },
  { id: "retrieval", label: "Top-K Retrieval", status: "pending" },
  { id: "llm", label: "LLM Processing", status: "pending" },
  { id: "response", label: "Response Ready", status: "pending" },
];

export function PipelineSimulator() {
  const [state, setState] = React.useState<SimulatorState>({
    query: "",
    topK: 4,
    isRunning: false,
    currentStep: 0,
    steps: INITIAL_STEPS,
    retrievedChunks: [],
    answer: "",
    sources: [],
    vectorDim: 384,
  });

  const updateStep = (stepId: string, status: PipelineStep["status"]) => {
    setState((prev) => ({
      ...prev,
      steps: prev.steps.map((step) =>
        step.id === stepId ? { ...step, status } : step
      ),
    }));
  };

  const resetSimulator = () => {
    setState({
      query: "",
      topK: 4,
      isRunning: false,
      currentStep: 0,
      steps: INITIAL_STEPS,
      retrievedChunks: [],
      answer: "",
      sources: [],
      vectorDim: 384,
    });
  };

  const runQuery = async () => {
    if (!state.query.trim()) return;

    setState((prev) => ({ ...prev, isRunning: true, currentStep: 0 }));
    
    // Reset steps
    setState((prev) => ({
      ...prev,
      steps: INITIAL_STEPS.map((step) => ({ ...step, status: "pending" })),
      retrievedChunks: [],
      answer: "",
      sources: [],
    }));

    // Step 1: Query Received
    updateStep("query", "active");
    await new Promise((resolve) => setTimeout(resolve, 500));
    updateStep("query", "completed");

    // Step 2: Embedding Model
    updateStep("embedding", "active");
    await new Promise((resolve) => setTimeout(resolve, 800));
    updateStep("embedding", "completed");

    // Step 3: Vector DB Search
    updateStep("search", "active");
    
    const payload: StreamPayload = {
      query: state.query,
      model: "llama3.2:3b",
      top_k: state.topK,
      hybrid: true,
    };

    let chunks: RetrievedChunk[] = [];
    let fullAnswer = "";
    const uniqueSources = new Set<string>();

    try {
      await streamAssistantChat(payload, {
        onContext: (data) => {
          chunks = (data.chunks || []).map((chunk: any) => ({
            chunk_id: chunk.metadata?.chunk_id || "",
            document_id: chunk.metadata?.document_id || "",
            filename: chunk.metadata?.filename || "Unknown",
            page: chunk.metadata?.page ? parseInt(chunk.metadata.page) : 1,
            paragraph_index: chunk.metadata?.paragraph_index ? parseInt(chunk.metadata.paragraph_index) : 1,
            content: chunk.document || "",
            score: chunk.distance ? 1 - chunk.distance : 0,
          }));
          
          chunks.forEach((chunk) => {
            uniqueSources.add(chunk.filename);
          });
          
          setState((prev) => ({
            ...prev,
            retrievedChunks: chunks,
            sources: Array.from(uniqueSources),
          }));
          
          updateStep("search", "completed");
          updateStep("retrieval", "active");
          setTimeout(() => updateStep("retrieval", "completed"), 500);
        },
        onToken: (token) => {
          fullAnswer += token;
          setState((prev) => ({ ...prev, answer: fullAnswer }));
        },
        onThinking: () => {
          updateStep("llm", "active");
        },
        onDone: () => {
          updateStep("llm", "completed");
          updateStep("response", "completed");
          setState((prev) => ({ ...prev, isRunning: false }));
        },
        onError: (message) => {
          console.error("Stream error:", message);
          setState((prev) => ({ ...prev, isRunning: false }));
        },
      });
    } catch (error) {
      console.error("Query failed:", error);
      setState((prev) => ({ ...prev, isRunning: false }));
    }
  };

  const generateVectorVisualization = () => {
    const bars = 20;
    return (
      <div className="flex items-end gap-1 h-16 mt-4">
        {Array.from({ length: bars }).map((_, i) => {
          const height = Math.random() * 100;
          return (
            <div
              key={i}
              className="w-2 bg-blue-500 rounded-sm transition-all duration-300"
              style={{ height: `${height}%` }}
            />
          );
        })}
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-background text-foreground p-6">
      <div className="max-w-7xl mx-auto">
        <div className="mb-6">
          <h1 className="text-3xl font-bold mb-2">RAG Pipeline Simulator</h1>
          <p className="text-muted-foreground">
            Visualize the retrieval-augmented generation pipeline in real-time
          </p>
        </div>

        {/* Controls */}
        <div className="bg-card border border-border rounded-lg p-4 mb-6 flex items-center gap-6">
          <div className="flex-1">
            <input
              type="text"
              placeholder="Enter your query..."
              value={state.query}
              onChange={(e) => setState((prev) => ({ ...prev, query: e.target.value }))}
              disabled={state.isRunning}
              className="w-full px-4 py-2 bg-background border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
              onKeyDown={(e) => e.key === "Enter" && runQuery()}
            />
          </div>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <label className="text-sm font-medium">Top-K:</label>
              <input
                type="range"
                min="1"
                max="12"
                value={state.topK}
                onChange={(e) => setState((prev) => ({ ...prev, topK: parseInt(e.target.value) }))}
                disabled={state.isRunning}
                className="w-24"
              />
              <span className="text-sm font-mono w-6">{state.topK}</span>
            </div>
            <button
              onClick={runQuery}
              disabled={state.isRunning || !state.query.trim()}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {state.isRunning ? "Running..." : "Run Query"}
            </button>
            <button
              onClick={resetSimulator}
              disabled={state.isRunning}
              className="px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-md disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              Reset
            </button>
          </div>
        </div>

        {/* 3-Column Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column: Query Input & Vector Visualization */}
          <div className="bg-card border border-border rounded-lg p-6">
            <h2 className="text-xl font-semibold mb-4">Query & Embedding</h2>
            
            <div className="space-y-4">
              <div>
                <h3 className="text-sm font-medium text-muted-foreground mb-2">Query Text</h3>
                <p className="text-sm bg-background border border-border rounded-md p-3 min-h-[60px]">
                  {state.query || "Enter a query to see the embedding visualization"}
                </p>
              </div>

              <div>
                <h3 className="text-sm font-medium text-muted-foreground mb-2">
                  Query Vector (Dim: {state.vectorDim})
                </h3>
                {state.query ? (
                  generateVectorVisualization()
                ) : (
                  <div className="h-16 bg-background border_BORDER rounded-md flex items-center justify-center text-muted-foreground text-sm">
                    Vector will appear here
                  </div>
                )}
              </div>

              <div>
                <h3 className="text-sm font-medium text-muted-foreground mb-2">Embedding Model</h3>
                <div className="text-sm bg-background border border-border rounded-md p-3">
                  <p className="font-mono">ChromaDB DefaultEmbeddingFunction</p>
                  <p className="text-muted-foreground text-xs mt-1">ONNX-based, 384 dimensions</p>
                </div>
              </div>
            </div>
          </div>

          {/* Middle Column: Step Tracker & Retrieved Chunks */}
          <div className="bg-card border border-border rounded-lg p-6">
            <h2 className="text-xl font-semibold mb-4">Pipeline Stages</h2>

            {/* Step Tracker */}
            <div className="space-y-3 mb-6">
              {state.steps.map((step, index) => (
                <div
                  key={step.id}
                  className={`flex items-center gap-3 p-3 rounded-md border ${
                    step.status === "active"
                      ? "border-blue-500 bg-blue-500/10"
                      : step.status === "completed"
                      ? "border-green-500 bg-green-500/10"
                      : "border-border bg-background"
                  }`}
                >
                  <div
                    className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
                      step.status === "completed"
                        ? "bg-green-500 text-white"
                        : step.status === "active"
                        ? "bg-blue-500 text-white"
                        : "bg-gray-600 text-gray-400"
                    }`}
                  >
                    {step.status === "completed" ? "✓" : index + 1}
                  </div>
                  <span className="text-sm font-medium">{step.label}</span>
                </div>
              ))}
            </div>

            {/* Retrieved Chunks */}
            <div>
              <h3 className="text-lg font-semibold mb-3">Top-K Retrieved Chunks</h3>
              {state.retrievedChunks.length > 0 ? (
                <div className="space-y-2 max-h-[400px] overflow-y-auto">
                  {state.retrievedChunks.map((chunk, index) => (
                    <div
                      key={chunk.chunk_id}
                      className="bg-background border border-border rounded-md p-3"
                    >
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-xs font-mono text-muted-foreground">
                          #{index + 1}
                        </span>
                        <span className="text-xs font-bold text-blue-400">
                          Score: {(chunk.score * 100).toFixed(1)}%
                        </span>
                      </div>
                      <div className="text-sm font-medium mb-1">
                        {chunk.filename}
                      </div>
                      <div className="text-xs text-muted-foreground mb-2">
                        Page {chunk.page}, Paragraph {chunk.paragraph_index}
                      </div>
                      <div className="text-xs bg-background border border-border rounded p-2 max-h-[80px] overflow-y-auto">
                        {chunk.content.substring(0, 150)}
                        {chunk.content.length > 150 && "..."}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-sm text-muted-foreground bg-background border border-border rounded-md p-4 text-center">
                  No chunks retrieved yet
                </div>
              )}
            </div>
          </div>

          {/* Right Column: Answer & Sources */}
          <div className="bg-card border border-border rounded-lg p-6">
            <h2 className="text-xl font-semibold mb-4">Response</h2>

            <div className="space-y-4">
              <div>
                <h3 className="text-sm font-medium text-muted-foreground mb-2">Grounded Answer</h3>
                <div className="bg-background border border-border rounded-md p-4 min-h-[200px] max-h-[400px] overflow-y-auto">
                  {state.answer ? (
                    <div className="text-sm whitespace-pre-wrap">{state.answer}</div>
                  ) : (
                    <div className="text-sm text-muted-foreground">
                      Answer will appear here after query completes
                    </div>
                  )}
                </div>
              </div>

              <div>
                <h3 className="text-sm font-medium text-muted-foreground mb-2">Cited Sources</h3>
                {state.sources.length > 0 ? (
                  <div className="space-y-2">
                    {state.sources.map((source, index) => (
                      <div
                        key={index}
                        className="bg-background border border-border rounded-md p-3 flex items-center gap-2"
                      >
                        <div className="w-2 h-2 bg-green-500 rounded-full" />
                        <span className="text-sm">{source}</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-sm text-muted-foreground bg-background border border-border rounded-md p-4 text-center">
                    No sources cited yet
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
