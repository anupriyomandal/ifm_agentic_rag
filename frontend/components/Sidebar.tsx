"use client";

import { MessageSquare, Plus, ChevronLeft, ChevronRight, Torus } from "lucide-react";
import type { Conversation } from "@/lib/types";

function timeAgo(date: Date) {
  const diff = Date.now() - date.getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

interface Props {
  conversations: Conversation[];
  activeId: string | null;
  open: boolean;
  onToggle: () => void;
  onNew: () => void;
  onSelect: (id: string) => void;
}

export function Sidebar({ conversations, activeId, open, onToggle, onNew, onSelect }: Props) {
  return (
    <aside
      className="relative flex flex-col flex-shrink-0 transition-all duration-300 ease-in-out"
      style={{
        width: open ? "280px" : "0px",
        background: "linear-gradient(160deg, #1e2f5c 0%, #273C6F 60%, #1a2848 100%)",
        overflow: "hidden",
      }}
    >
      {/* Subtle noise texture */}
      <div
        className="absolute inset-0 pointer-events-none opacity-[0.04]"
        style={{
          backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.75' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E")`,
          backgroundSize: "200px 200px",
        }}
      />

      <div className="flex flex-col h-full w-[280px]">
        {/* Logo */}
        <div className="flex items-center gap-3 px-5 pt-6 pb-5 border-b border-white/10">
          <div className="flex items-center justify-center w-9 h-9 rounded-lg bg-ceat-orange flex-shrink-0">
            <Torus size={18} className="text-white" />
          </div>
          <div>
            <div
              className="text-white leading-none tracking-[0.12em] uppercase"
              style={{ fontFamily: "var(--font-barlow)", fontSize: "1.2rem", fontWeight: 700 }}
            >
              CEAT
            </div>
            <div className="text-white/50 text-[10px] tracking-widest uppercase mt-0.5">
              IFM Tyre Advisor
            </div>
          </div>
        </div>

        {/* New chat */}
        <div className="px-4 pt-4 pb-2">
          <button
            onClick={onNew}
            className="w-full flex items-center gap-2.5 px-4 py-2.5 rounded-lg text-sm font-medium
              bg-white/10 text-white hover:bg-ceat-orange hover:text-white
              border border-white/10 hover:border-ceat-orange
              transition-all duration-200 group"
          >
            <Plus size={16} className="group-hover:rotate-90 transition-transform duration-200" />
            New conversation
          </button>
        </div>

        {/* History */}
        <div className="flex-1 overflow-y-auto px-3 py-2 space-y-1">
          {conversations.length === 0 ? (
            <p className="text-white/30 text-xs text-center mt-8 px-4">
              Your conversations will appear here
            </p>
          ) : (
            conversations.map((c) => (
              <button
                key={c.id}
                onClick={() => onSelect(c.id)}
                className={`w-full text-left px-3 py-2.5 rounded-lg transition-all duration-150 group
                  ${
                    c.id === activeId
                      ? "bg-white/15 border border-white/20"
                      : "hover:bg-white/8 border border-transparent"
                  }`}
              >
                <div className="flex items-start gap-2.5">
                  <MessageSquare
                    size={13}
                    className={`mt-0.5 flex-shrink-0 ${
                      c.id === activeId ? "text-ceat-orange" : "text-white/40"
                    }`}
                  />
                  <div className="flex-1 min-w-0">
                    <div className="text-white/90 text-xs font-medium truncate leading-snug">
                      {c.title}
                    </div>
                    <div className="text-white/35 text-[10px] mt-0.5">
                      {timeAgo(c.createdAt)} · {c.messages.filter((m) => m.role === "user").length} msg
                    </div>
                  </div>
                </div>
              </button>
            ))
          )}
        </div>

        {/* Footer */}
        <div className="px-4 py-4 border-t border-white/10">
          <div className="text-white/25 text-[10px] text-center tracking-wide uppercase">
            Powered by GPT-4.1 · CEAT RPG
          </div>
        </div>
      </div>

      {/* Toggle button */}
      <button
        onClick={onToggle}
        className="absolute top-1/2 -right-3 -translate-y-1/2 z-20
          w-6 h-6 rounded-full bg-ceat-blue border-2 border-white/20
          flex items-center justify-center text-white
          hover:bg-ceat-orange transition-colors duration-200 shadow-lg"
      >
        {open ? <ChevronLeft size={12} /> : <ChevronRight size={12} />}
      </button>
    </aside>
  );
}
