#!/usr/bin/env node

import http from "node:http";

const host = process.env.DEV_TRANSLATION_HOST ?? "127.0.0.1";
const port = Number(process.env.DEV_TRANSLATION_PORT ?? "8001");

function readJson(request) {
  return new Promise((resolve, reject) => {
    let body = "";
    request.setEncoding("utf8");
    request.on("data", (chunk) => {
      body += chunk;
    });
    request.on("end", () => {
      try {
        resolve(body ? JSON.parse(body) : {});
      } catch (error) {
        reject(error);
      }
    });
  });
}

const server = http.createServer(async (request, response) => {
  if (request.method === "GET" && request.url === "/health") {
    response.writeHead(200, { "content-type": "application/json" });
    response.end(JSON.stringify({ ok: true, provider: "dev_translation_mock" }));
    return;
  }

  if (request.method === "POST" && request.url === "/translate") {
    try {
      const payload = await readJson(request);
      response.writeHead(200, { "content-type": "application/json" });
      response.end(
        JSON.stringify({
          translated_text: String(payload.text ?? ""),
          source_lang: payload.source_lang ?? "auto",
          target_lang: payload.target_lang ?? "en",
          provider: "dev_translation_mock",
          cached: false
        })
      );
    } catch {
      response.writeHead(400, { "content-type": "application/json" });
      response.end(JSON.stringify({ error: "invalid_json" }));
    }
    return;
  }

  response.writeHead(404, { "content-type": "application/json" });
  response.end(JSON.stringify({ error: "not_found" }));
});

server.listen(port, host, () => {
  process.stdout.write(`dev translation mock listening on http://${host}:${port}\n`);
});
