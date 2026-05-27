import { notFound } from "next/navigation";
import { ChatWindow } from "@/components/dev-chat/ChatWindow";

export default function DevChatPage() {
  if (process.env.NEXT_PUBLIC_ENABLE_DEV_TOOLS !== "true") {
    notFound();
  }
  return <ChatWindow />;
}
