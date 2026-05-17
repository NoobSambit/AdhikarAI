import { readFileSync, existsSync } from "node:fs";
import assert from "node:assert/strict";

const api = readFileSync(new URL("../lib/api.ts", import.meta.url), "utf8");
const dashboard = readFileSync(new URL("../app/dashboard/page.tsx", import.meta.url), "utf8");
const dashboardLayout = readFileSync(new URL("../app/dashboard/layout.tsx", import.meta.url), "utf8");
const adminQuality = readFileSync(new URL("../app/admin/quality/page.tsx", import.meta.url), "utf8");

assert.ok(existsSync(new URL("../app/page.tsx", import.meta.url)), "beneficiary PWA route must remain present");
assert.match(api, /DashboardRole/, "dashboard role types should be shared in API client");
assert.match(api, /credentials: "include"/, "dashboard must use httpOnly cookie session");
assert.doesNotMatch(api, /localStorage\.setItem\(["'].*token/i, "JWT must not be stored in localStorage");
assert.match(dashboardLayout, /DashboardShell/, "dashboard should use the operator shell");
assert.match(dashboard, /Follow-ups due/, "dashboard home should prioritize follow-ups");
assert.match(dashboard, /role === "operator"/, "dashboard navigation should react to role");
assert.match(adminQuality, /markQualityFlagReviewed/, "quality page should expose review workflow");

console.log("Phase 5 frontend static checks passed");
