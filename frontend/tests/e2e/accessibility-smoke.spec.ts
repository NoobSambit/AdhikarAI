import { expect, test } from "@playwright/test";
import { assertBackendReady, expectVisibleFocus, loginAs, readMetadata } from "./helpers";

test.describe("accessibility and responsive smoke", () => {
  test("PWA controls have accessible names and work at mobile width", async ({ page }) => {
    await assertBackendReady();
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto("/");

    await expect(page.getByRole("button", { name: "Start recording" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Send typed message" })).toBeVisible();
    await expect(page.getByRole("navigation", { name: "Main" })).toBeVisible();
    await page.keyboard.press("Tab");
    await expectVisibleFocus(page);
  });

  test("dashboard navigation and controls work at desktop and tablet widths", async ({ page }) => {
    await assertBackendReady();
    await loginAs(page, "operator");
    const metadata = readMetadata();

    await page.setViewportSize({ width: 1280, height: 900 });
    await page.goto("/dashboard");
    await expect(page.getByRole("navigation", { name: "Dashboard navigation" })).toBeVisible();
    await expect(page.getByRole("link", { name: /Beneficiaries/ })).toBeVisible();

    await page.keyboard.press("Tab");
    await expectVisibleFocus(page);

    await page.setViewportSize({ width: 820, height: 900 });
    await page.goto("/dashboard/beneficiaries");
    await expect(page.getByPlaceholder("Name, phone, village")).toBeVisible();
    await expect(page.getByRole("button", { name: "Search" })).toBeVisible();

    await page.goto(`/dashboard/beneficiaries/${metadata.assigned_beneficiary_id}`);
    await expect(page.getByRole("heading", { name: "Local Beneficiary Assigned" })).toBeVisible();
    await expect(page.getByLabel("Add note")).toBeVisible();
    await page.keyboard.press("Tab");
    await expectVisibleFocus(page);
  });
});
