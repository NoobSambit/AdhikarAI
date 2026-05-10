"use client";

export function DebugStatePanel({ value }: { value: unknown }) {
  return (
    <details>
      <summary>Debug</summary>
      <pre>{JSON.stringify(value, null, 2)}</pre>
    </details>
  );
}
