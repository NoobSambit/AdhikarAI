#!/usr/bin/env node

import http from "node:http";

const host = process.env.DEV_TTS_HOST ?? "127.0.0.1";
const port = Number(process.env.DEV_TTS_PORT ?? "8002");

function wavSilence(durationSeconds = 0.35) {
  const sampleRate = 16_000;
  const bitsPerSample = 16;
  const channels = 1;
  const sampleCount = Math.floor(sampleRate * durationSeconds);
  const dataSize = sampleCount * channels * (bitsPerSample / 8);
  const buffer = Buffer.alloc(44 + dataSize);

  buffer.write("RIFF", 0);
  buffer.writeUInt32LE(36 + dataSize, 4);
  buffer.write("WAVE", 8);
  buffer.write("fmt ", 12);
  buffer.writeUInt32LE(16, 16);
  buffer.writeUInt16LE(1, 20);
  buffer.writeUInt16LE(channels, 22);
  buffer.writeUInt32LE(sampleRate, 24);
  buffer.writeUInt32LE(sampleRate * channels * (bitsPerSample / 8), 28);
  buffer.writeUInt16LE(channels * (bitsPerSample / 8), 32);
  buffer.writeUInt16LE(bitsPerSample, 34);
  buffer.write("data", 36);
  buffer.writeUInt32LE(dataSize, 40);
  return buffer;
}

const audio = wavSilence();

const server = http.createServer((request, response) => {
  if (request.method === "GET" && request.url === "/health") {
    response.writeHead(200, { "content-type": "application/json" });
    response.end(JSON.stringify({ ok: true, provider: "dev_tts_mock" }));
    return;
  }

  if (request.method === "POST" && request.url === "/synthesize") {
    request.resume();
    response.writeHead(200, { "content-type": "audio/wav" });
    response.end(audio);
    return;
  }

  response.writeHead(404, { "content-type": "application/json" });
  response.end(JSON.stringify({ error: "not_found" }));
});

server.listen(port, host, () => {
  process.stdout.write(`dev TTS mock listening on http://${host}:${port}\n`);
});
