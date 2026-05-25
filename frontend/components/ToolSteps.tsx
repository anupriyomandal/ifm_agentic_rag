"use client";

import { Database, Code2, Hash, BarChart2, MapPin, CheckCircle2, Loader2 } from "lucide-react";
import type { ToolStep } from "@/lib/types";

const TOOL_META: Record<string, { icon: React.ElementType; description: string }> = {
  get_schema:       { icon: Database,  description: "Loading data schema" },
  run_pandas:       { icon: Code2,     description: "Running analysis on dataset" },
  get_value_counts: { icon: Hash,      description: "Checking column values" },
  get_column_stats: { icon: BarChart2, description: "Computing statistics" },
  get_office_names: { icon: MapPin,    description: "Resolving geography" },
};

function formatArgs(args: Record<string, unknown>): string {
  const entries = Object.entries(args);
  if (entries.length === 0) return "()";
  const parts = entries.map(([k, v]) => {
    const val = String(v).replace(/\n/g, " ").trim();
    const truncated = val.length > 90 ? val.slice(0, 90) + "…" : val;
    return `${k}="${truncated}"`;
  });
  return `(${parts.join(", ")})`;
}

interface Props {
  steps: ToolStep[];
}

export function ToolSteps({ steps }: Props) {
  if (steps.length === 0) return null;

  const isRunning = steps.some((s) => s.status === "running");

  return (
    <div className="mb-3 rounded-xl border border-slate-200 bg-white overflow-hidden text-[11px]">
      {/* Header */}
      <div className="flex items-center gap-2 px-4 py-2.5 bg-slate-50 border-b border-slate-200">
        {isRunning ? (
          <Loader2 size={11} className="text-ceat-orange animate-spin flex-shrink-0" />
        ) : (
          <CheckCircle2 size={11} className="text-emerald-500 flex-shrink-0" />
        )}
        <span className="font-medium text-slate-500">
          {isRunning ? "Thinking…" : `Done · ${steps.length} tool call${steps.length !== 1 ? "s" : ""}`}
        </span>
      </div>

      {/* Steps */}
      <div className="px-4 py-3 space-y-3">
        {steps.map((step, i) => {
          const meta = TOOL_META[step.name] ?? { icon: Code2, description: "Running tool" };
          const Icon = meta.icon;
          const isActive = step.status === "running";
          const isDone = step.status === "done";

          return (
            <div key={i} className="flex gap-3">
              {/* Timeline */}
              <div className="flex flex-col items-center flex-shrink-0">
                <div
                  className={`w-5 h-5 rounded-full flex items-center justify-center flex-shrink-0 ${
                    isActive
                      ? "bg-ceat-orange/10 ring-1 ring-ceat-orange/30"
                      : "bg-ceat-blue/10"
                  }`}
                >
                  {isActive ? (
                    <Loader2 size={10} className="text-ceat-orange animate-spin" />
                  ) : (
                    <Icon size={10} className="text-ceat-blue" />
                  )}
                </div>
                {i < steps.length - 1 && (
                  <div className="w-px flex-1 bg-slate-200 mt-1 min-h-[12px]" />
                )}
              </div>

              {/* Content */}
              <div className="flex-1 min-w-0 pt-0.5">
                {/* Function call */}
                <div className="font-mono leading-relaxed break-all">
                  <span className="font-semibold text-ceat-blue">{step.name}</span>
                  <span className="text-slate-400">{formatArgs(step.args as Record<string, unknown>)}</span>
                </div>

                {/* Status line */}
                {isActive && (
                  <div className="flex items-center gap-1.5 mt-1 text-[10px] text-ceat-orange">
                    <span
                      className="w-1 h-1 rounded-full bg-ceat-orange inline-block"
                      style={{ animation: "pulse-dot 1s ease-in-out infinite" }}
                    />
                    {meta.description}…
                  </div>
                )}
                {isDone && step.preview && (
                  <div className="mt-1 text-[10px] text-slate-400 font-mono truncate">
                    ↳ {step.preview}
                  </div>
                )}
                {isDone && !step.preview && (
                  <div className="mt-0.5 text-[10px] text-emerald-500">✓ Done</div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
