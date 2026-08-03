"use client";

import * as React from "react";
import { PipelineSimulator } from "@/components/pipeline-simulator";

export default function SimulatorPage() {
  return (
    <div className="min-h-screen bg-background">
      <PipelineSimulator />
    </div>
  );
}
