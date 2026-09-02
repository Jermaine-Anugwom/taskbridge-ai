import { expect, test } from "@playwright/test";

test("opens on the workflow map with synthetic labeling", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByText("SYNTHETIC DEMONSTRATION")).toBeVisible();
  await expect(page.getByRole("heading", { name: "See the work before changing it." })).toBeVisible();
  await expect(page.getByLabel("Current workflow")).toBeVisible();
  await expect(page.getByLabel("Proposed pilot workflow")).toBeVisible();
});

test("switches scenarios and refuses unnecessary AI", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("button", { name: /Invoice exceptions/ }).click();
  await page.getByRole("button", { name: /Decide/ }).click();
  await expect(page.getByText("Use deterministic checks. Do not add AI to the decision.")).toBeVisible();
  await expect(page.getByText("RULES", { exact: true })).toBeVisible();
});

test("explains the same workflow for multiple audiences", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("button", { name: /Explain/ }).click();
  await expect(page.getByRole("heading", { name: "You stop doing the same sorting twice." })).toBeVisible();
  await page.getByRole("tab", { name: "IT + security" }).click();
  await expect(page.getByRole("heading", { name: "The data path and authority are explicit." })).toBeVisible();
});

test("moves between audience tabs with arrow keys", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("button", { name: /Explain/ }).click();
  const employeeTab = page.getByRole("tab", { name: "Employee" });
  await employeeTab.focus();
  await page.keyboard.press("ArrowRight");
  await expect(page.getByRole("tab", { name: "Manager" })).toBeFocused();
  await expect(page.getByRole("heading", { name: "The common path becomes consistent." })).toBeVisible();
});

test("runs the synthetic pilot without external actions", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("button", { name: /Simulate/ }).click();
  await page.getByRole("button", { name: "Run synthetic pilot" }).click();
  await expect(page.getByRole("button", { name: /Running synthetic records/ })).toBeDisabled();
  await expect(page.getByText("EXTERNAL ACTIONS", { exact: true })).toBeVisible();
  await expect(page.getByText("DISABLED", { exact: true })).toBeVisible();
  await expect(page.getByText("Synthetic pilot completed. Results are ready.")).toBeAttached();
});

test("supports keyboard navigation", async ({ page }) => {
  await page.goto("/");
  await page.keyboard.press("Tab");
  await expect(page.getByRole("link", { name: "Skip to workshop" })).toBeFocused();
  await page.keyboard.press("Enter");
  await expect(page.locator("#workshop")).toBeInViewport();
});

test("renders mobile without horizontal overflow", async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== "mobile");
  await page.goto("/");
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth);
  expect(overflow).toBe(false);
  await expect(page.getByRole("navigation", { name: "Workflow improvement stages" })).toBeVisible();
  const workflowSteps = page.getByLabel("Current workflow").getByRole("listitem");
  await expect(workflowSteps).toHaveCount(4);
  const laneOverflow = await page.getByLabel("Current workflow").locator("ol").evaluate((element) => element.scrollWidth > element.clientWidth);
  expect(laneOverflow).toBe(false);
  await workflowSteps.nth(3).scrollIntoViewIfNeeded();
  await expect(workflowSteps.nth(3)).toBeInViewport();
});
