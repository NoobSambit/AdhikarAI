import { expect, test } from "@playwright/test";
import { API_URL, assertBackendReady, expectVisibleFocus, readMetadata, useSession } from "./helpers";

test.describe("operator dashboard", () => {
  test.beforeEach(async ({ context }) => {
    await assertBackendReady();
    await useSession(context, "operator");
  });

  test("loads beneficiary list, creates and searches beneficiary, and verifies operator workflows", async ({ page }) => {
    const metadata = readMetadata();
    const createdName = `Playwright Beneficiary ${Date.now()}`;
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

    const frontendDetail = await page.request.get(`/dashboard/beneficiaries/${created.id}`);
    if (frontendDetail.status() !== 404) {
      await page.goto(`/dashboard/beneficiaries/${created.id}`);
      await expect(page.getByText(createdName)).toBeVisible();
    }

    const noteResponse = await page.request.post(`${API_URL}/dashboard/beneficiaries/${metadata.assigned_beneficiary_id}/notes`, {
      data: { note: "Playwright operator note" }
    });
    expect(noteResponse.ok(), await noteResponse.text()).toBeTruthy();

    const followupResponse = await page.request.post(`${API_URL}/dashboard/beneficiaries/${metadata.assigned_beneficiary_id}/followups`, {
      data: { due_date: tomorrow, reason: "Playwright follow-up" }
    });
    expect(followupResponse.ok(), await followupResponse.text()).toBeTruthy();

    const detailResponse = await page.request.get(`${API_URL}/dashboard/beneficiaries/${metadata.assigned_beneficiary_id}`);
    expect(detailResponse.ok(), await detailResponse.text()).toBeTruthy();
    const detail = await detailResponse.json();
    expect(detail.notes.some((note: { note: string }) => note.note === "Playwright operator note")).toBeTruthy();
    expect(detail.followups.some((followup: { reason?: string }) => followup.reason === "Playwright follow-up")).toBeTruthy();

    const statusId = detail.application_statuses[0]?.id;
    expect(statusId).toBeTruthy();
    const statusResponse = await page.request.patch(`${API_URL}/dashboard/application-status/${statusId}`, {
      data: { status: "submitted", notes: "Playwright status update" }
    });
    expect(statusResponse.ok(), await statusResponse.text()).toBeTruthy();

    const deniedResponse = await page.request.get(`${API_URL}/dashboard/beneficiaries/${metadata.unassigned_beneficiary_id}`);
    expect(deniedResponse.status()).toBe(403);
    const deniedBody = await deniedResponse.json();
    expect(deniedBody.code ?? deniedBody.error?.code).toBe("BENEFICIARY_NOT_ASSIGNED");

    await page.goto("/dashboard");
    await page.keyboard.press("Tab");
    await expectVisibleFocus(page);
  });
});
