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
assert.match(home, /My details/, "profile tab should expose editable beneficiary details");
assert.match(home, /Profile completeness/, "profile tab should show local completeness");
for (const field of ["display_name", "state_code", "district", "village", "age", "gender", "occupation_type", "annual_income", "ration_card_type", "land_holding_acres", "has_land_record", "has_bank_account"]) {
  assert.match(home, new RegExp(field), `profile tab should include ${field}`);
}
assert.match(home, /Save details/, "profile tab should save local profile facts");
assert.match(home, /saveInlineStatus/, "profile save status should appear near save actions");
assert.match(home, /Changes are not saved yet\./, "profile save area should show unsaved state");
assert.match(home, /Saved on this phone at/, "profile save action should show an inline timestamp");
assert.match(home, /Find schemes/, "profile tab should submit saved facts to the agent");
assert.match(home, /Guest mode\. No account has been created yet\./, "profile tab should make guest account state explicit");
assert.match(home, /sendOtp/, "profile tab should expose beneficiary OTP account creation");
assert.match(home, /verifyOtp/, "profile tab should verify beneficiary OTP login");
assert.match(home, /SearchableSelect/, "profile tab should use explicit searchable dropdown controls");
assert.match(home, /role="listbox"/, "location selector should render a real dropdown menu");
assert.match(home, /Open \$\{props\.label\} list/, "location selector should expose a list-opening button");
const locations = readFileSync(new URL("../lib/indiaLocations.ts", import.meta.url), "utf8");
assert.match(locations, /West Bengal/, "India location data should include states");
assert.match(locations, /Purba Medinipur/, "India location data should include state-specific districts");
assert.match(locations, /Nandigram/, "India location data should include village suggestions for known districts");
assert.match(api, /credentials: "include"/, "JWT cookie must be used without localStorage token storage");
assert.doesNotMatch(api, /localStorage\.setItem\(["'].*token/i, "JWT must not be stored in localStorage");
assert.match(offline, /cached_schemes/, "IndexedDB should cache schemes");
assert.match(offline, /sync_queue/, "IndexedDB should include sync queue");
assert.match(offline, /retry_count/, "sync queue should include retry metadata");
assert.match(sw, /offline\.html/, "service worker should provide offline fallback");
assert.ok(existsSync(new URL("../public/manifest.json", import.meta.url)), "PWA manifest should exist");

console.log("Phase 4 frontend static checks passed");
