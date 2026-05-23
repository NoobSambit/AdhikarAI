import { expect, test } from "@playwright/test";
import { API_URL, assertBackendReady, useSession } from "./helpers";

test.describe("super admin", () => {
  test.beforeEach(async ({ context }) => {
    await assertBackendReady();
    await useSession(context, "super_admin");
  });

  test("loads admin pages and previews a scheme draft through the implemented endpoint", async ({ page }) => {
    await page.goto("/admin/quality");
    await expect(page.getByRole("heading", { name: "Quality Flags" })).toBeVisible();

    await page.goto("/admin/unmatched-queries");
    await expect(page.getByRole("heading", { name: "Zero-match Review" })).toBeVisible();
    await expect(page.getByText("goat shed support")).toBeVisible();

    await page.goto("/admin/analytics");
    await expect(page.getByRole("heading", { name: "Analytics" })).toBeVisible();

    const draftResponse = await page.request.post(`${API_URL}/admin/scheme-drafts`, {
      data: {
        change_summary: "Playwright draft preview smoke.",
        draft_payload: {
          scheme: {
            id: `playwright_scheme_${Date.now()}`,
            name: "Playwright Scheme Preview",
            description: "Scheme used only for local Playwright preview smoke.",
            plain_language_summary: "Preview smoke scheme.",
            ministry: "Local Test Ministry",
            state_code: "IN-BR",
            benefit_type: "cash",
            benefit_amount: "INR 1",
            source_url: "https://example.test/playwright"
          },
          eligibility_rule: {
            min_age: 18,
            state_codes: ["IN-BR"],
            required_documents: [
              {
                name: "Identity proof",
                is_mandatory: true,
                accepted_substitutes: []
              }
            ]
          }
        }
      }
    });
    expect(draftResponse.ok(), await draftResponse.text()).toBeTruthy();
    const draft = await draftResponse.json();

    const previewResponse = await page.request.post(`${API_URL}/admin/scheme-drafts/${draft.draft_id}/preview`);
    expect(previewResponse.ok(), await previewResponse.text()).toBeTruthy();
    const preview = await previewResponse.json();
    expect(preview.validation_result.errors).toEqual([]);
    expect(preview.sample_impact.profiles_tested).toBe(0);

    await page.goto("/admin/schemes");
    await expect(page.getByText("Scheme draft APIs are available under /admin/scheme-drafts.")).toBeVisible();
  });
});
