import { notFound } from "next/navigation";
import { VoiceDevWindow } from "@/components/voice/VoiceDevWindow";

export default function DevVoicePage() {
  if (process.env.NEXT_PUBLIC_ENABLE_DEV_TOOLS !== "true") {
    notFound();
  }
  return <VoiceDevWindow />;
}
