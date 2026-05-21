import { test, expect } from '@playwright/test';

test.describe('GitHub Trending 页面', () => {
  test('Trending 页面正常加载', async ({ page }) => {
    await page.goto('/trending?since=daily');

    // 等待仓库列表加载
    const repos = page.locator('article.Box-row');
    const count = await repos.count();
    expect(count).toBeGreaterThan(0);

    // 页面标题包含 Trending
    const title = await page.title();
    expect(title).toContain('Trending');
  });

  test('至少显示一个 trending 仓库', async ({ page }) => {
    await page.goto('/trending?since=daily');

    // GitHub trending 仓库在 article.Box-row 中
    const firstRepo = page.locator('article.Box-row').first();
    await expect(firstRepo).toBeVisible({ timeout: 10_000 });
  });

  test('页面可以滚动查看更多内容', async ({ page }) => {
    await page.goto('/trending?since=daily');

    // 滚动到底部
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    await page.waitForTimeout(500);

    // 页面高度应该增加了滚动空间
    const scrollY = await page.evaluate(() => window.scrollY);
    expect(scrollY).toBeGreaterThan(0);
  });
});
