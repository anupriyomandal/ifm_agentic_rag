export type ToolStep = {
  name: string;
  args: Record<string, string>;
  preview?: string;
  status: "running" | "done";
};

export type Chart = {
  image: string;
  title: string;
};

export type Message = {
  id: string;
  role: "user" | "assistant";
  content: string;
  toolSteps?: ToolStep[];
  charts?: Chart[];
  isStreaming?: boolean;
};

export type Conversation = {
  id: string;
  title: string;
  messages: Message[];
  createdAt: Date;
};

export type SSEEvent =
  | { type: "tool_call"; name: string; args: Record<string, string> }
  | { type: "tool_result"; name: string; preview: string }
  | { type: "chart"; image: string; title: string }
  | { type: "content"; text: string }
  | { type: "done" }
  | { type: "error"; message: string };
