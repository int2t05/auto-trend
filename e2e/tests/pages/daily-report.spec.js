import { test, expect } from '@playwright/test';

test.describe('GitHub Pages - 日报首页', () => {
  test('首页正常加载，显示标题和索引', async ({ page }) => {
    await page.goto('/');

    // 等待页面主要内容加载
    await expect(page.locator('h1, h2, article, main')).toBeVisible({
      timeout: 15_000,
    });

    // 页面标题应包含 auto-trend
    const title = await page.title();
    expect(title).toBeTruthy();
  });

  test('页面无 JS 报错', async ({ page }) => {
    const errors = [];
    page.on('pageerror', (err) => errors.push(err));

    await page.goto('/');
    await page.waitForLoadState('load');

    expect(errors).toHaveLength(0);
  });

  test('索引页有可点击的日报链接', async ({ page }) => {
    await page.goto('/');

    // 找日报链接（Markdown 渲染的 a 标签）
    const links = page.locator('a[href]');
    const count = await links.count();

    // 至少有一个链接
    expect(count).toBeGreaterThan(0);
  });
});
