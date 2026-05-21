const { chromium } = require('@playwright/test');
const dotenv = require('dotenv');
const path = require('path');

dotenv.config({ path: path.resolve(__dirname, '.env') });

(async () => {
  // 1. 启动浏览器（headless: false = 你能看到浏览器窗口）
  const browser = await chromium.launch({
    headless: false,   // 显示浏览器窗口，设为 true 则后台运行
    slowMo: 300,       // 每个操作慢 300ms，方便看
  });

  const context = await browser.newContext({
    locale: 'zh-CN',
    viewport: { width: 1440, height: 900 },
  });

  const page = await context.newPage();

  // 2. 打开 GitHub Trending
  console.log('→ 打开 GitHub Trending...');
  await page.goto('https://github.com/trending?since=daily');
  await page.waitForTimeout(1000);

  // 3. 截图
  await page.screenshot({ path: 'screenshots/trending.png', fullPage: true });
  console.log('→ 截图已保存: screenshots/trending.png');

  // 4. 抓取前 5 个项目名称
  const repos = await page.locator('article.Box-row h2').evaluateAll((els) =>
    els.slice(0, 5).map((el) => el.textContent.trim().replace(/\s+/g, ' '))
  );
  console.log('\n前5个Trending项目:');
  repos.forEach((r, i) => console.log(`  ${i + 1}. ${r}`));

  // 5. 点进第一个项目
  console.log('\n→ 点击第一个项目...');
  await page.locator('article.Box-row h2 a').first().click();
  await page.waitForTimeout(1500);
  console.log('→ 当前 URL:', page.url());
  await page.screenshot({ path: 'screenshots/repo-detail.png' });

  // 6. 回到 Trending，切换到本周榜
  console.log('\n→ 切换到 "本周" 榜单...');
  await page.goBack();
  await page.waitForTimeout(500);

  // 点击 "This week" 链接（用多种方式列出来供你选）
  try {
    // 方式1: getByRole
    await page.getByRole('link', { name: /week/i }).click();
  } catch {
    // 方式2: 直接拼 URL
    await page.goto('https://github.com/trending?since=weekly');
  }
  await page.waitForTimeout(1000);
  await page.screenshot({ path: 'screenshots/trending-weekly.png', fullPage: true });
  console.log('→ 周榜截图已保存');

  // 7. 关闭浏览器
  console.log('\n完成。3秒后关闭浏览器...');
  await page.waitForTimeout(3000);
  await browser.close();
  console.log('→ 浏览器已关闭');
})();
