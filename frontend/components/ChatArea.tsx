"use client";

import { useEffect, useRef } from "react";
import { RotateCcw, Torus } from "lucide-react";
import { MessageBubble } from "./MessageBubble";
import { SuggestedQueries } from "./SuggestedQueries";
import { ChatInput } from "./ChatInput";
import type { Message } from "@/lib/types";

interface Props {
  messages: Message[];
  isStreaming: boolean;
  onSend: (text: string) => void;
  onClear: () => void;
}

export function ChatArea({ messages, isStreaming, onSend, onClear }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <main className="flex flex-col h-screen bg-slate-50">
      {/* Header */}
      <header className="flex items-center gap-3 px-6 py-3.5 bg-white border-b border-slate-200 flex-shrink-0">
        {/* Logo mark */}
        <div
          className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0"
          style={{ background: "linear-gradient(135deg, #273C6F 0%, #0055AA 100%)" }}
        >
          <Torus size={15} className="text-ceat-orange" />
        </div>

        {/* Title */}
        <div>
          <div
            className="text-ceat-dark leading-none tracking-wide"
            style={{ fontFamily: "var(--font-barlow)", fontSize: "1.05rem", fontWeight: 700 }}
          >
            IFM Tyre Advisor
          </div>
          <div className="text-slate-400 text-[10px] mt-0.5 leading-none">CEAT · GPT-4.1</div>
        </div>

        {/* Right side */}
        <div className="ml-auto flex items-center gap-3">
          <div className="flex items-center gap-1.5 text-[10px] text-slate-400">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
            Live
          </div>
          {messages.length > 0 && (
            <button
              onClick={onClear}
              disabled={isStreaming}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium
                text-slate-500 hover:bg-slate-100 disabled:opacity-40 transition-colors"
            >
              <RotateCcw size={12} />
              Clear
            </button>
          )}
        </div>
      </header>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto">
        {messages.length === 0 ? (
          <SuggestedQueries onSelect={onSend} />
        ) : (
          <div className="max-w-3xl mx-auto px-4 py-6 space-y-5">
            {messages.map((msg) => (
              <MessageBubble key={msg.id} message={msg} />
            ))}
            <div ref={bottomRef} />
          </div>
        )}
      </div>

      {/* Input */}
      <div className="bg-white border-t border-slate-200 flex-shrink-0">
        <div className="max-w-3xl mx-auto">
          <ChatInput onSend={onSend} disabled={isStreaming} />
        </div>
      </div>
    </main>
  );
}
