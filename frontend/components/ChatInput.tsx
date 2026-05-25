"use client";

import { useRef, useState, useEffect } from "react";
import { SendHorizonal, Loader2 } from "lucide-react";

interface Props {
  onSend: (text: string) => void;
  disabled?: boolean;
}

export function ChatInput({ onSend, disabled }: Props) {
  const [text, setText] = useState("");
  const ref = useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 180)}px`;
  }, [text]);

  const submit = () => {
    const trimmed = text.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setText("");
  };

  const onKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  };

  return (
    <div className="px-4 pb-4 pt-2">
      <div
        className={`flex items-end gap-2 rounded-2xl bg-white border shadow-sm transition-all duration-200
          ${disabled ? "border-slate-200 opacity-70" : "border-slate-200 focus-within:border-ceat-blue/50 focus-within:shadow-md"}`}
      >
        <textarea
          ref={ref}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={onKeyDown}
          disabled={disabled}
          rows={1}
          placeholder="Ask about CPKM, mileage, tyre wear, brand comparisons…"
          className="flex-1 resize-none bg-transparent px-4 py-3.5 text-sm text-slate-800
            placeholder:text-slate-400 focus:outline-none leading-relaxed min-h-[50px]"
          style={{ fontFamily: "var(--font-ibm)" }}
        />
        <button
          onClick={submit}
          disabled={!text.trim() || disabled}
          className="flex-shrink-0 m-2 w-9 h-9 rounded-xl flex items-center justify-center
            transition-all duration-200 disabled:opacity-40 disabled:cursor-not-allowed
            bg-ceat-orange hover:bg-orange-500 active:scale-95 shadow-sm"
        >
          {disabled ? (
            <Loader2 size={16} className="text-white animate-spin" />
          ) : (
            <SendHorizonal size={16} className="text-white" />
          )}
        </button>
      </div>
      <p className="text-center text-[10px] text-slate-400 mt-2">
        Shift+Enter for new line · Enter to send
      </p>
    </div>
  );
}
