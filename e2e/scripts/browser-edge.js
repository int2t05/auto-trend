const { chromium } = require('@playwright/test');

const EDGE_PROFILE =
  'C:\\Users\\Admin\\AppData\\Local\\Microsoft\\Edge\\User Data';

// 命令行传 --keep-open 则保持浏览器打开，否则跑完自动关闭
const keepOpen = process.argv.includes('--keep-open');

(async () => {
  console.log('启动 Edge（使用你的登录态）...');
  console.log('⚠ 请先关闭所有 Edge 窗口！\n');

  const context = await chromium.launchPersistentContext(EDGE_PROFILE, {
    channel: 'msedge',
    headless: false,
    viewport: { width: 1440, height: 900 },
  });

  const page = await context.newPage();

  // 1. 访问 GitHub
  console.log('→ 打开 GitHub...');
  await page.goto('https://github.com');

  const loggedIn = await page
    .locator('meta[name="user-login"]')
    .getAttribute('content')
    .catch(() => null);

  if (loggedIn) {
    console.log(`→ 已登录 GitHub，当前用户: ${loggedIn}`);
  } else {
    console.log('→ 未检测到 GitHub 登录态，请在浏览器里手动登录一次');
    console.log('  （登录后 cookie 自动保存到 Edge profile）');
    await page.waitForTimeout(30_000);
  }

  // 2. 访问 GitHub Pages 日报
  console.log('\n→ 打开日报...');
  await page.goto('https://int2t05.github.io/auto-trend/');
  await page.waitForTimeout(1000);

  // 3. 截图
  await page.screenshot({ path: 'screenshots/edge-daily.png', fullPage: true });
  console.log('→ 截图: screenshots/edge-daily.png');

  if (keepOpen) {
    console.log('\n✅ 浏览器保持打开，按 Ctrl+C 关闭\n');
    await new Promise(() => {});
  } else {
    console.log('\n→ 操作完成，关闭浏览器');
    await context.close();
    console.log('→ 浏览器已关闭');
  }
})();
