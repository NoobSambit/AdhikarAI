"use client";

import { Pause, Play, RotateCcw } from "lucide-react";
import { useRef, useState } from "react";
import { resolveAudioUrl } from "@/lib/api";

export function TtsPlayer(props: { audioUrl?: string; transcript: string; autoPlay?: boolean }) {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [playing, setPlaying] = useState(false);
  const [speed, setSpeed] = useState(1);

  function applySpeed(value: number) {
    setSpeed(value);
    if (audioRef.current) {
      audioRef.current.playbackRate = value;
    }
  }

  function togglePlay() {
    if (!audioRef.current) return;
    if (audioRef.current.paused) {
      audioRef.current.play();
      setPlaying(true);
    } else {
      audioRef.current.pause();
      setPlaying(false);
    }
  }

  function replay() {
    if (!audioRef.current) return;
    audioRef.current.currentTime = 0;
    audioRef.current.play();
    setPlaying(true);
  }

  return (
    <div className="ttsPlayer">
      {props.audioUrl ? (
        <audio
          ref={audioRef}
          src={resolveAudioUrl(props.audioUrl)}
          autoPlay={props.autoPlay}
          onEnded={() => setPlaying(false)}
          onPlay={() => setPlaying(true)}
          onPause={() => setPlaying(false)}
        />
      ) : null}
      <div className="ttsControls">
        <button className="iconButton" type="button" onClick={togglePlay} disabled={!props.audioUrl} aria-label={playing ? "Pause" : "Play"}>
          {playing ? <Pause size={18} /> : <Play size={18} />}
        </button>
        <button className="iconButton" type="button" onClick={replay} disabled={!props.audioUrl} aria-label="Replay">
          <RotateCcw size={18} />
        </button>
        {[0.75, 1, 1.5].map((value) => (
          <button key={value} className={speed === value ? "speed active" : "speed"} type="button" onClick={() => applySpeed(value)}>
            {value}x
          </button>
        ))}
      </div>
      <p>{props.transcript}</p>
    </div>
  );
}
