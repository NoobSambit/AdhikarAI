import { readFileSync, existsSync } from "node:fs";
import assert from "node:assert/strict";

const home = readFileSync(new URL("../app/page.tsx", import.meta.url), "utf8");
const api = readFileSync(new URL("../lib/api.ts", import.meta.url), "utf8");
const offline = readFileSync(new URL("../lib/offlineDb.ts", import.meta.url), "utf8");
const sw = readFileSync(new URL("../public/sw.js", import.meta.url), "utf8");

assert.match(home, /AudioRecorder/, "home voice CTA should render first-screen voice flow");
assert.match(home, /bottomNav/, "bottom navigation should be present");
assert.match(home, /Home[\s\S]*My Schemes[\s\S]*History[\s\S]*Profile/, "bottom navigation should have icon labels");
assert.match(home, /Login with phone to save this scheme/, "guest restricted actions should open login prompt");
assert.match(home, /high_contrast_enabled/, "accessibility settings should persist");
assert.match(api, /credentials: "include"/, "JWT cookie must be used without localStorage token storage");
assert.doesNotMatch(api, /localStorage\.setItem\(["'].*token/i, "JWT must not be stored in localStorage");
assert.match(offline, /cached_schemes/, "IndexedDB should cache schemes");
assert.match(offline, /sync_queue/, "IndexedDB should include sync queue");
assert.match(offline, /retry_count/, "sync queue should include retry metadata");
assert.match(sw, /offline\.html/, "service worker should provide offline fallback");
assert.ok(existsSync(new URL("../public/manifest.json", import.meta.url)), "PWA manifest should exist");

console.log("Phase 4 frontend static checks passed");
