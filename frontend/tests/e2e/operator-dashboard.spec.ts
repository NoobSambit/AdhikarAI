import { expect, test } from "@playwright/test";
import { API_URL, assertBackendReady, expectVisibleFocus, loginAs, readMetadata } from "./helpers";

test.describe("operator dashboard", () => {
  test.beforeEach(async ({ page }) => {
    await assertBackendReady();
    await loginAs(page, "operator");
  });

  test("loads beneficiary list, creates and searches beneficiary, and verifies operator workflows", async ({ page }) => {
    const metadata = readMetadata();
    const createdName = `Playwright Beneficiary ${Date.now()}`;
    const noteText = `Playwright operator note ${Date.now()}`;
    const followupReason = `Playwright follow-up ${Date.now()}`;
    const tomorrow = new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString().slice(0, 10);

    await page.goto("/dashboard");
    await expect(page.getByRole("heading", { name: "Operator Dashboard" })).toBeVisible();
    await expect(page.getByText("Local Beneficiary Assigned")).toBeVisible();

    await page.setViewportSize({ width: 820, height: 900 });
    await expect(page.getByRole("link", { name: /Beneficiaries/ })).toBeVisible();

    await page.goto("/dashboard/beneficiaries/new");
    await page.getByLabel("Name").fill(createdName);
    await page.getByLabel("Phone").fill(`+9198${Date.now().toString().slice(-8)}`);
    await page.getByLabel("State").fill("IN-BR");
    await page.getByLabel("District").fill("Patna");
    await page.getByLabel("Village").fill("E2E Village");
    await page.getByRole("spinbutton", { name: "Age" }).fill("41");
    await page.getByRole("textbox", { name: "Gender" }).fill("female");
    await page.getByRole("spinbutton", { name: "Annual income" }).fill("72000");
    await page.getByRole("button", { name: "Save" }).click();
    await expect(page.getByText("Beneficiary saved.")).toBeVisible();

    await page.goto("/dashboard/beneficiaries");
    await page.getByPlaceholder("Name, phone, village").fill(createdName);
    await page.getByRole("button", { name: "Search" }).click();
    await expect(page.getByRole("link", { name: createdName })).toBeVisible();

    const listResponse = await page.request.get(`${API_URL}/dashboard/beneficiaries?q=${encodeURIComponent(createdName)}`);
    expect(listResponse.ok(), await listResponse.text()).toBeTruthy();
    const created = (await listResponse.json()).items[0];
    expect(created.name).toBe(createdName);

    await page.goto(`/dashboard/beneficiaries/${created.id}`);
    await expect(page.getByRole("heading", { name: createdName })).toBeVisible();
    await expect(page.getByText("E2E Village")).toBeVisible();

    await page.goto(`/dashboard/beneficiaries/${metadata.assigned_beneficiary_id}`);
    await expect(page.getByRole("heading", { name: "Local Beneficiary Assigned" })).toBeVisible();
    await expect(page.getByText("+919000000001")).toBeVisible();
    await expect(page.getByText("Rampur")).toBeVisible();

    await page.getByLabel("Add note").fill(noteText);
    await page.getByRole("button", { name: "Add note" }).click();
    await expect(page.getByRole("status")).toContainText("Note added.");
    await expect(page.getByText(noteText)).toBeVisible();

    await page.getByLabel("Due date").fill(tomorrow);
    await page.getByLabel("Reason").fill(followupReason);
    await page.getByRole("button", { name: "Add follow-up" }).click();
    await expect(page.getByRole("status")).toContainText("Follow-up added.");
    await expect(page.getByText(followupReason)).toBeVisible();

    const detailResponse = await page.request.get(`${API_URL}/dashboard/beneficiaries/${metadata.assigned_beneficiary_id}`);
    expect(detailResponse.ok(), await detailResponse.text()).toBeTruthy();
    const detail = await detailResponse.json();
    expect(detail.notes.some((note: { note: string }) => note.note === noteText)).toBeTruthy();
    expect(detail.followups.some((followup: { reason?: string }) => followup.reason === followupReason)).toBeTruthy();

    const statusId = detail.application_statuses[0]?.id;
    expect(statusId).toBeTruthy();
    const statusSelect = page.getByLabel(`Update ${detail.application_statuses[0].scheme_id} application status`);
    await statusSelect.selectOption("submitted");
    await expect(page.getByRole("status")).toContainText("Application status updated.");

    await page.getByRole("button", { name: "Run eligibility" }).click();
    await expect(page.getByRole("status")).toContainText("Eligibility run complete.");

    const deniedResponse = await page.request.get(`${API_URL}/dashboard/beneficiaries/${metadata.unassigned_beneficiary_id}`);
    expect(deniedResponse.status()).toBe(403);
    const deniedBody = await deniedResponse.json();
    expect(deniedBody.code ?? deniedBody.error?.code).toBe("BENEFICIARY_NOT_ASSIGNED");

    await page.goto(`/dashboard/beneficiaries/${metadata.unassigned_beneficiary_id}`);
    await expect(page.getByText("You do not have access to this beneficiary.")).toBeVisible();

    await page.goto("/dashboard");
    await page.keyboard.press("Tab");
    await expectVisibleFocus(page);

    await page.getByRole("button", { name: "Sign out" }).click();
    await expect(page).toHaveURL(/\/dashboard\/login/);
    const meResponse = await page.request.get(`${API_URL}/dashboard/me`);
    expect(meResponse.status()).toBe(401);
  });
});
