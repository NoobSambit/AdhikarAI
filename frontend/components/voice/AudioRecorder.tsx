"use client";

import { Mic, Square } from "lucide-react";
import { useRef, useState } from "react";
import { LanguageCode } from "@/lib/api";
import { browserAsrSupported, startBrowserAsr } from "@/lib/audio/browserAsr";

export type RecordingMode = "push_to_talk" | "continuous";

export interface AudioMetadata {
  durationMs: number;
  mimeType: string;
}

const SILENCE_MS = Number(process.env.NEXT_PUBLIC_SILENCE_MS ?? 1500);
const SILENCE_THRESHOLD = Number(process.env.NEXT_PUBLIC_SILENCE_THRESHOLD ?? 0.018);
const BROWSER_FALLBACK_AFTER_MS = Number(process.env.NEXT_PUBLIC_BROWSER_ASR_FALLBACK_AFTER_MS ?? 2000);

export function AudioRecorder(props: {
  mode: RecordingMode;
  languageCode: LanguageCode;
  onVoiceTurn: (blob: Blob, metadata: AudioMetadata) => Promise<void>;
  onFallbackText: (text: string) => Promise<void>;
  onAmplitudes: (values: number[]) => void;
  onStatus: (status: string, fallbackVisible?: boolean) => void;
}) {
  const [recording, setRecording] = useState(false);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<BlobPart[]>([]);
  const startedAtRef = useRef(0);
  const audioContextRef = useRef<AudioContext | null>(null);
  const rafRef = useRef<number | null>(null);
  const silenceStartedRef = useRef<number | null>(null);

  async function start() {
    if (recording) return;
    const stream = await navigator.mediaDevices.getUserMedia({
      audio: { channelCount: 1, sampleRate: 48000, noiseSuppression: true }
    });
    const mimeType = MediaRecorder.isTypeSupported("audio/webm") ? "audio/webm" : "";
    const recorder = new MediaRecorder(stream, mimeType ? { mimeType } : undefined);
    recorderRef.current = recorder;
    chunksRef.current = [];
    startedAtRef.current = Date.now();
    recorder.ondataavailable = (event) => chunksRef.current.push(event.data);
    recorder.onstop = async () => {
      stream.getTracks().forEach((track) => track.stop());
      stopMetering();
      const blob = new Blob(chunksRef.current, { type: recorder.mimeType || "audio/webm" });
      setRecording(false);
      await props.onVoiceTurn(blob, { durationMs: Date.now() - startedAtRef.current, mimeType: blob.type });
    };
    recorder.start();
    setRecording(true);
    props.onStatus("Recording...");
    startMetering(stream);
    if (browserAsrSupported()) {
      window.setTimeout(async () => {
        if (!recorderRef.current || recorderRef.current.state !== "recording") return;
        try {
          const text = await startBrowserAsr(props.languageCode, BROWSER_FALLBACK_AFTER_MS);
          if (text.trim()) {
            await props.onFallbackText(text.trim());
          }
        } catch {
          props.onStatus("Internet is slow. Please type your message or try again.", true);
        }
      }, BROWSER_FALLBACK_AFTER_MS);
    } else {
      props.onStatus("You can type your message here.", true);
    }
  }

  function stop() {
    const recorder = recorderRef.current;
    if (recorder && recorder.state === "recording") {
      recorder.stop();
    }
  }

  function startMetering(stream: MediaStream) {
    const context = new AudioContext();
    audioContextRef.current = context;
    const source = context.createMediaStreamSource(stream);
    const analyser = context.createAnalyser();
    analyser.fftSize = 256;
    source.connect(analyser);
    const data = new Uint8Array(analyser.frequencyBinCount);
    const amplitudes: number[] = [];
    const tick = () => {
      analyser.getByteTimeDomainData(data);
      const amp = data.reduce((sum, value) => sum + Math.abs(value - 128), 0) / data.length / 128;
      amplitudes.push(amp);
      props.onAmplitudes([...amplitudes.slice(-24)]);
      if (props.mode === "continuous") {
        if (amp < SILENCE_THRESHOLD) {
          silenceStartedRef.current ??= Date.now();
          if (Date.now() - silenceStartedRef.current >= SILENCE_MS) stop();
        } else {
          silenceStartedRef.current = null;
        }
      }
      rafRef.current = window.requestAnimationFrame(tick);
    };
    tick();
  }

  function stopMetering() {
    if (rafRef.current) window.cancelAnimationFrame(rafRef.current);
    audioContextRef.current?.close();
    audioContextRef.current = null;
  }

  const isPush = props.mode === "push_to_talk";
  return (
    <button
      className={recording ? "recordButton active" : "recordButton"}
      type="button"
      onPointerDown={isPush ? start : undefined}
      onPointerUp={isPush ? stop : undefined}
      onPointerCancel={isPush ? stop : undefined}
      onClick={!isPush ? (recording ? stop : start) : undefined}
      aria-label={recording ? "Stop recording" : "Start recording"}
    >
      {recording ? <Square size={24} /> : <Mic size={24} />}
      <span>{recording ? "Stop" : isPush ? "Hold to talk" : "Tap to talk"}</span>
    </button>
  );
}
