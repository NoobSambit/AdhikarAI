import { readFileSync, existsSync } from "node:fs";
import assert from "node:assert/strict";

const api = readFileSync(new URL("../lib/api.ts", import.meta.url), "utf8");
const dashboard = readFileSync(new URL("../app/dashboard/page.tsx", import.meta.url), "utf8");
const dashboardLayout = readFileSync(new URL("../app/dashboard/layout.tsx", import.meta.url), "utf8");
const beneficiaryDetail = readFileSync(new URL("../app/dashboard/beneficiaries/[id]/page.tsx", import.meta.url), "utf8");
const beneficiaryDetailClient = readFileSync(new URL("../app/dashboard/beneficiaries/[id]/BeneficiaryDetailClient.tsx", import.meta.url), "utf8");
const adminQuality = readFileSync(new URL("../app/admin/quality/page.tsx", import.meta.url), "utf8");

assert.ok(existsSync(new URL("../app/page.tsx", import.meta.url)), "beneficiary PWA route must remain present");
assert.match(api, /DashboardRole/, "dashboard role types should be shared in API client");
assert.match(api, /credentials: "include"/, "dashboard must use httpOnly cookie session");
assert.doesNotMatch(api, /localStorage\.setItem\(["'].*token/i, "JWT must not be stored in localStorage");
assert.match(dashboardLayout, /DashboardShell/, "dashboard should use the operator shell");
assert.match(dashboard, /Follow-ups due/, "dashboard home should prioritize follow-ups");
assert.match(dashboard, /role === "operator"/, "dashboard navigation should react to role");
assert.ok(existsSync(new URL("../app/dashboard/beneficiaries/[id]/page.tsx", import.meta.url)), "beneficiary detail route must exist");
assert.match(beneficiaryDetail, /BeneficiaryDetailClient/, "beneficiary detail route should render the client workflow");
assert.match(beneficiaryDetailClient, /getDashboardBeneficiary/, "beneficiary detail route should load the dashboard detail API");
assert.match(beneficiaryDetailClient, /BENEFICIARY_NOT_ASSIGNED|ORG_SCOPE_DENIED/, "beneficiary detail route should handle backend access errors");
assert.match(beneficiaryDetailClient, /maxLength=\{5000\}/, "beneficiary detail note input should enforce the PRD note limit");
assert.match(adminQuality, /markQualityFlagReviewed/, "quality page should expose review workflow");

console.log("Phase 5 frontend static checks passed");
