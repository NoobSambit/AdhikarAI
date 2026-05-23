import { expect, test } from "@playwright/test";
import { API_URL, assertBackendReady, readMetadata, useSession } from "./helpers";

test.describe("NGO admin dashboard", () => {
  test.beforeEach(async ({ context }) => {
    await assertBackendReady();
    await useSession(context, "ngo_admin");
  });

  test("loads organisation-scoped beneficiary list and denies cross-org detail", async ({ page }) => {
    const metadata = readMetadata();

    await page.goto("/dashboard");
    await expect(page.getByRole("heading", { name: "Operator Dashboard" })).toBeVisible();
    await expect(page.getByText("Organisation-level beneficiary support")).toBeVisible();

    await page.goto("/dashboard/beneficiaries");
    await expect(page.getByRole("link", { name: "Local Beneficiary Assigned" })).toBeVisible();
    await expect(page.getByText("Other NGO Beneficiary")).toHaveCount(0);

    const listResponse = await page.request.get(`${API_URL}/dashboard/beneficiaries`);
    expect(listResponse.ok(), await listResponse.text()).toBeTruthy();
    const list = await listResponse.json();
    expect(list.items.some((item: { id: string }) => item.id === metadata.assigned_beneficiary_id)).toBeTruthy();
    expect(list.items.some((item: { id: string }) => item.id === metadata.other_org_beneficiary_id)).toBeFalsy();

    const deniedResponse = await page.request.get(`${API_URL}/dashboard/beneficiaries/${metadata.other_org_beneficiary_id}`);
    expect(deniedResponse.status()).toBe(403);
    const deniedBody = await deniedResponse.json();
    expect(deniedBody.code ?? deniedBody.error?.code).toBe("ORG_SCOPE_DENIED");
  });
});
