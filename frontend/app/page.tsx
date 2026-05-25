"use client";

import { useState, useCallback } from "react";
import { ChatArea } from "@/components/ChatArea";
import type { Message } from "@/lib/types";
import { streamChat } from "@/lib/api";

function makeId() {
  return Math.random().toString(36).slice(2, 10);
}

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);

  const clearChat = useCallback(() => {
    if (!isStreaming) setMessages([]);
  }, [isStreaming]);

  const sendMessage = useCallback(
    async (text: string) => {
      const userMsg: Message = { id: makeId(), role: "user", content: text };
      const assistantMsgId = makeId();
      const assistantMsg: Message = {
        id: assistantMsgId,
        role: "assistant",
        content: "",
        toolSteps: [],
        isStreaming: true,
      };

      const historySnapshot = messages.filter((m) => !m.isStreaming);
      setMessages((prev) => [...prev, userMsg, assistantMsg]);
      setIsStreaming(true);

      try {
        const stream = streamChat(text, historySnapshot);

        for await (const event of stream) {
          if (event.type === "tool_call") {
            setMessages((prev) =>
              prev.map((m) =>
                m.id === assistantMsgId
                  ? {
                      ...m,
                      toolSteps: [
                        ...(m.toolSteps ?? []),
                        { name: event.name, args: event.args, status: "running" as const },
                      ],
                    }
                  : m
              )
            );
          } else if (event.type === "tool_result") {
            setMessages((prev) =>
              prev.map((m) => {
                if (m.id !== assistantMsgId) return m;
                const steps = [...(m.toolSteps ?? [])];
                const last = steps.length - 1;
                if (last >= 0) steps[last] = { ...steps[last], preview: event.preview, status: "done" };
                return { ...m, toolSteps: steps };
              })
            );
          } else if (event.type === "content") {
            setMessages((prev) =>
              prev.map((m) =>
                m.id === assistantMsgId ? { ...m, content: m.content + event.text } : m
              )
            );
          } else if (event.type === "done" || event.type === "error") {
            const errorText = event.type === "error" ? `\n\n⚠️ Error: ${event.message}` : "";
            setMessages((prev) =>
              prev.map((m) =>
                m.id === assistantMsgId
                  ? { ...m, content: m.content + errorText, isStreaming: false }
                  : m
              )
            );
            setIsStreaming(false);
          }
        }
      } catch (err) {
        const msg = err instanceof Error ? err.message : "Unknown error";
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantMsgId
              ? { ...m, content: `⚠️ Failed to reach the server: ${msg}`, isStreaming: false }
              : m
          )
        );
        setIsStreaming(false);
      }
    },
    [messages]
  );

  return (
    <div className="h-screen overflow-hidden">
      <ChatArea
        messages={messages}
        isStreaming={isStreaming}
        onSend={sendMessage}
        onClear={clearChat}
      />
    </div>
  );
}
