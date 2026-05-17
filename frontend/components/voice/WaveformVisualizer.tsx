"use client";

export function WaveformVisualizer(props: { amplitudes: number[]; isActive: boolean }) {
  const bars = props.amplitudes.length ? props.amplitudes : Array.from({ length: 24 }, () => 0.08);
  return (
    <div className={`waveform ${props.isActive ? "active" : ""}`} aria-hidden="true">
      {bars.slice(-24).map((value, index) => (
        <span key={index} style={{ height: `${Math.max(8, Math.round(value * 80))}px` }} />
      ))}
    </div>
  );
}
