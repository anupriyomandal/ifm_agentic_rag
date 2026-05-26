"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Torus, User } from "lucide-react";
import { ToolSteps } from "./ToolSteps";
import type { Message } from "@/lib/types";

function ThinkingDots() {
  return (
    <div className="flex items-center gap-1.5 py-1">
      <span className="text-xs text-slate-400 mr-1">Analyzing</span>
      {[0, 1, 2].map((i) => (
        <span
          key={i}
          className="w-1.5 h-1.5 rounded-full bg-ceat-orange inline-block"
          style={{
            animation: "pulse-dot 1.2s ease-in-out infinite",
            animationDelay: `${i * 0.2}s`,
          }}
        />
      ))}
    </div>
  );
}

interface Props {
  message: Message;
}

export function MessageBubble({ message }: Props) {
  const isUser = message.role === "user";

  if (isUser) {
    return (
      <div className="flex justify-end animate-fade-up">
        <div className="flex items-end gap-2.5 max-w-[75%] min-w-0">
          <div
            className="px-4 py-3 rounded-2xl rounded-br-sm text-sm text-white leading-relaxed shadow-sm break-words"
            style={{ background: "linear-gradient(135deg, #0055AA 0%, #0066CC 100%)" }}
          >
            {message.content}
          </div>
          <div className="flex-shrink-0 w-7 h-7 rounded-full bg-ceat-blue/10 border border-ceat-blue/20 flex items-center justify-center mb-0.5">
            <User size={13} className="text-ceat-blue" />
          </div>
        </div>
      </div>
    );
  }

  // Assistant
  return (
    <div className="flex justify-start animate-fade-up">
      <div className="flex items-end gap-2.5 max-w-[82%] min-w-0 w-full">
        {/* Avatar */}
        <div className="flex-shrink-0 w-7 h-7 rounded-full bg-ceat-dark flex items-center justify-center mb-0.5 shadow-sm">
          <Torus size={13} className="text-ceat-orange" />
        </div>

        <div className="flex-1 min-w-0 overflow-hidden">
          {/* Tool steps */}
          {message.toolSteps && message.toolSteps.length > 0 && (
            <ToolSteps steps={message.toolSteps} />
          )}

          {/* Charts */}
          {message.charts && message.charts.length > 0 && (
            <div className="mb-3 space-y-3">
              {message.charts.map((chart, i) => (
                <div key={i} className="rounded-xl border border-slate-200 bg-white shadow-sm overflow-hidden">
                  {chart.title && (
                    <div className="px-4 pt-3 text-xs font-semibold text-ceat-dark">{chart.title}</div>
                  )}
                  <img src={chart.image} alt={chart.title || "Chart"} className="w-full h-auto" />
                </div>
              ))}
            </div>
          )}

          {/* Message content */}
          <div className="bg-white rounded-2xl rounded-bl-sm border border-slate-200 shadow-sm px-4 py-3 overflow-x-auto">
            {message.isStreaming && !message.content ? (
              <ThinkingDots />
            ) : message.content ? (
              <div className="prose-ifm">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {message.content}
                </ReactMarkdown>
              </div>
            ) : null}

            {/* Streaming cursor */}
            {message.isStreaming && message.content && (
              <span
                className="inline-block w-0.5 h-3.5 bg-ceat-orange ml-0.5 align-middle"
                style={{ animation: "pulse 1s step-end infinite" }}
              />
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
