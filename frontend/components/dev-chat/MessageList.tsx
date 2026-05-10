"use client";

export interface DevMessage {
  role: "user" | "assistant";
  content: string;
}

export function MessageList({ messages }: { messages: DevMessage[] }) {
  return (
    <div className="messages" aria-live="polite">
      {messages.map((message, index) => (
        <div className={`message ${message.role}`} key={`${message.role}-${index}`}>
          {message.content}
        </div>
      ))}
    </div>
  );
}
