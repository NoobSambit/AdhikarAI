import { LanguageCode } from "@/lib/api";

type SpeechRecognitionCtor = new () => SpeechRecognition;

interface SpeechRecognition extends EventTarget {
  lang: string;
  interimResults: boolean;
  maxAlternatives: number;
  start: () => void;
  stop: () => void;
  onresult: ((event: SpeechRecognitionEvent) => void) | null;
  onerror: (() => void) | null;
}

interface SpeechRecognitionEvent {
  results: ArrayLike<{ 0: { transcript: string; confidence: number } }>;
}

export function browserAsrSupported() {
  return typeof window !== "undefined" && ("SpeechRecognition" in window || "webkitSpeechRecognition" in window);
}

export function startBrowserAsr(languageCode: LanguageCode, timeoutMs: number): Promise<string> {
  return new Promise((resolve, reject) => {
    const ctor = ((window as unknown as Record<string, SpeechRecognitionCtor>).SpeechRecognition ||
      (window as unknown as Record<string, SpeechRecognitionCtor>).webkitSpeechRecognition);
    if (!ctor) {
      reject(new Error("Browser ASR unsupported"));
      return;
    }
    const recognition = new ctor();
    recognition.lang = `${languageCode}-IN`;
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;
    const timer = window.setTimeout(() => {
      recognition.stop();
      reject(new Error("Browser ASR timeout"));
    }, timeoutMs);
    recognition.onresult = (event) => {
      window.clearTimeout(timer);
      resolve(event.results[0][0].transcript);
    };
    recognition.onerror = () => {
      window.clearTimeout(timer);
      reject(new Error("Browser ASR failed"));
    };
    recognition.start();
  });
}
