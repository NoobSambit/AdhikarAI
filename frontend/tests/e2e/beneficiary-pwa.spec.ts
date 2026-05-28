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

  test("saves guest profile details locally and sends them through agent message", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto("/");

    await page.getByRole("button", { name: "Profile" }).click();
    await expect(page.getByRole("heading", { name: "My details" })).toBeVisible();

    await page.getByLabel("Display name").fill("Sita Devi");
    await page.getByLabel("State").fill("Bihar");
    await page.getByLabel("District").fill("Gaya");
    await page.getByLabel("Village").fill("Rampur");
    await page.getByLabel("Age").fill("35");
    await page.getByLabel("Gender").selectOption("female");
    await page.getByLabel("Occupation").fill("farmer");
    await page.getByLabel("Annual income").fill("72000");
    await page.getByLabel("Ration card type").selectOption("bpl");
    await page.getByLabel("Land acres").fill("1.5");
    await page.getByLabel("Has land record").check();
    await page.getByLabel("Has bank account").check();
    await page.getByRole("button", { name: "Save details" }).click();
    await expect(page.getByText("Saved on this phone.")).toBeVisible();

    await page.reload();
    await page.getByRole("button", { name: "Profile" }).click();
    await expect(page.getByLabel("Display name")).toHaveValue("Sita Devi");
    await expect(page.getByLabel("State")).toHaveValue("Bihar");

    const messageResponse = page.waitForResponse((response) => response.url().includes("/agent/message"));
    await page.getByRole("button", { name: "Find schemes" }).click();
    const response = await messageResponse;
    expect(response.ok(), await response.text()).toBeTruthy();

    await expect(page.locator(".turn.assistant, .schemeCard").first()).toBeVisible();
  });
});
