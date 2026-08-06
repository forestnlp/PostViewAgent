import { expect, test } from "@playwright/test";

import { mockLangGraphAPI } from "./utils/mock-api";

test.describe("Landing page", () => {
  test("renders the hero section", async ({ page }) => {
    await page.goto("/");

    // 邮览官定制页面：h1 包含"邮览官"
    await expect(page.locator("h1")).toHaveCount(1);
    await expect(page.locator("h1")).toContainText("邮览官");

    // "开始使用"按钮
    await expect(page.getByRole("link", { name: /开始使用/ })).toBeVisible();
  });

  for (const width of [320, 375, 390]) {
    test(`does not overflow at ${width}px width`, async ({ page }) => {
      await page.setViewportSize({ width, height: 812 });
      await page.goto("/");

      await expect
        .poll(() => page.evaluate(() => document.documentElement.scrollWidth))
        .toBeLessThanOrEqual(width);
      await expect(page.locator("main").first()).toBeInViewport();
    });
  }

  test("开始使用 link navigates to workspace", async ({ page }) => {
    mockLangGraphAPI(page);

    await page.goto("/");

    const getStarted = page.getByRole("link", { name: /开始使用/ });
    await getStarted.click();

    // Should redirect to /workspace
    await page.waitForURL("**/workspace**");
    await expect(page).toHaveURL(/\/workspace/);
  });
});
