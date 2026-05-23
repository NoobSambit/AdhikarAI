import { expect, test } from "@playwright/test";
import { assertBackendReady, expectNoJwtInLocalStorage, expectVisibleFocus } from "./helpers";

test.describe("beneficiary PWA", () => {
  test.beforeEach(async () => {
    await assertBackendReady();
  });

  test("loads, supports typed guest flow, keeps scheme UI stable, and avoids localStorage JWTs", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto("/");

    await expect(page.getByLabel("Voice home")).toBeVisible();
    await expect(page.getByLabel("Type your problem")).toBeVisible();
    await expect(page.getByRole("button", { name: "Send typed message" })).toBeDisabled();

    await page.getByLabel("Type your problem").fill("I am a small farmer from Bihar with low income.");
    const messageResponse = page.waitForResponse((response) => response.url().includes("/agent/message"));
    await page.getByRole("button", { name: "Send typed message" }).click();
    const response = await messageResponse;
    expect(response.ok(), await response.text()).toBeTruthy();
    const body = await response.json();
    expect(["question", "result", "clarification", "error", "state"]).toContain(body.type);

    await expect(page.locator(".turn.assistant, .schemeCard").first()).toBeVisible();
    await page.getByRole("button", { name: "My Schemes" }).click();
    await expect(page.getByRole("heading", { name: "PM-KISAN" })).toBeVisible();
    await expect(page.getByRole("button", { name: /Hear / }).first()).toBeVisible();

    await page.locator(".checkItem").first().click();
    await expect(page.locator(".schemeCard").first()).toBeVisible();

    await expectNoJwtInLocalStorage(page);

    await page.keyboard.press("Tab");
    await expectVisibleFocus(page);
  });
});
