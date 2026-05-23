import { BrowserContext, expect, Page } from "@playwright/test";
import fs from "node:fs";
import path from "node:path";

export const API_URL = process.env.E2E_API_URL ?? "http://127.0.0.1:8000";
export const COOKIE_DIR = process.env.E2E_COOKIE_DIR ?? "/tmp/adhikarai-local-e2e";

export type SessionRole = "operator" | "ngo_admin" | "super_admin" | "beneficiary";

export interface E2eMetadata {
  organisation_id: string;
  other_organisation_id: string;
  operator_member_id: string;
  ngo_admin_member_id: string;
  super_admin_member_id: string;
  assigned_beneficiary_id: string;
  unassigned_beneficiary_id: string;
  other_org_beneficiary_id: string;
  cookie_dir: string;
}

export function readMetadata(): E2eMetadata {
  const metadataPath = path.join(COOKIE_DIR, "metadata.json");
  if (!fs.existsSync(metadataPath)) {
    throw new Error(`Missing ${metadataPath}. Run backend local E2E seed first.`);
  }
  return JSON.parse(fs.readFileSync(metadataPath, "utf-8")) as E2eMetadata;
}

export async function assertBackendReady() {
  const response = await fetch(`${API_URL}/health`);
  expect(response.ok, `FastAPI must be running at ${API_URL}`).toBeTruthy();
}

export async function useSession(context: BrowserContext, role: SessionRole) {
  const cookiePath = path.join(COOKIE_DIR, `${role}.cookie`);
  if (!fs.existsSync(cookiePath)) {
    throw new Error(`Missing ${cookiePath}. Run backend local E2E seed first.`);
  }
  const line = fs
    .readFileSync(cookiePath, "utf-8")
    .split("\n")
    .find((entry) => entry.includes("\tadhikarai_session\t"));
  if (!line) {
    throw new Error(`No adhikarai_session cookie found in ${cookiePath}.`);
  }
  const parts = line.split("\t");
  const token = parts[parts.length - 1];
  await context.addCookies([
    { name: "adhikarai_session", value: token, domain: "127.0.0.1", path: "/", httpOnly: true, sameSite: "Lax" },
    { name: "adhikarai_session", value: token, domain: "localhost", path: "/", httpOnly: true, sameSite: "Lax" }
  ]);
}

export async function expectNoJwtInLocalStorage(page: Page) {
  const entries = await page.evaluate(() => Object.entries(window.localStorage));
  for (const [key, value] of entries) {
    expect(key, `localStorage key ${key} must not store auth material`).not.toMatch(/jwt|token|auth|session/i);
    expect(value, `localStorage value for ${key} must not look like a JWT`).not.toMatch(/^[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+$/);
  }
}

export async function expectVisibleFocus(page: Page) {
  const focused = page.locator(":focus");
  await expect(focused).toBeVisible();
  const focusStyle = await focused.evaluate((element) => {
    const style = window.getComputedStyle(element);
    return {
      outlineStyle: style.outlineStyle,
      outlineWidth: style.outlineWidth,
      outlineColor: style.outlineColor,
      boxShadow: style.boxShadow
    };
  });
  expect(
    focusStyle.outlineStyle !== "none" && focusStyle.outlineWidth !== "0px",
    `focused element should expose a visible outline: ${JSON.stringify(focusStyle)}`
  ).toBeTruthy();
}
