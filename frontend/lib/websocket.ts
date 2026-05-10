export function chatWebSocketUrl() {
  return `${process.env.NEXT_PUBLIC_WS_BASE_URL ?? "ws://localhost:8000"}/ws/chat`;
}
