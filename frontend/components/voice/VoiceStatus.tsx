"use client";

export function VoiceStatus(props: { status: string; progress: number; fallbackVisible: boolean }) {
  return (
    <div className="voiceStatus" role="status" aria-live="polite">
      <span>{props.status}</span>
      <div className="progress" aria-label="Upload progress">
        <span style={{ width: `${props.progress}%` }} />
      </div>
      {props.fallbackVisible ? <p className="fallbackText">You can type your message here.</p> : null}
    </div>
  );
}
