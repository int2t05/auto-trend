const { chromium } = require('@playwright/test');

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });

  // ============================
  // 读 GitHub Trending 页面内容
  // ============================
  console.log('→ 打开 GitHub Trending...\n');
  await page.goto('https://github.com/trending?since=daily');

  // 1. 页面标题
  console.log('【标题】', await page.title());

  // 2. 全文纯文本（不截图）
  const fullText = await page.locator('body').innerText();
  console.log('【全文长度】', fullText.length, '字符');

  // 3. 结构化提取：每个项目的 owner/name/desc/stars
  const repos = await page.locator('article.Box-row').evaluateAll((rows) =>
    rows.slice(0, 5).map((row) => {
      const h2 = row.querySelector('h2');
      const desc = row.querySelector('p');
      const lang = row.querySelector('[itemprop="programmingLanguage"]');
      const stars = row.querySelectorAll('a')[2]; // stars link
      return {
        name: h2?.textContent?.trim().replace(/\s+/g, ' ') || '',
        desc: desc?.textContent?.trim() || '',
        lang: lang?.textContent?.trim() || '',
        stars: stars?.textContent?.trim() || '',
      };
    })
  );

  console.log('【Top 5 结构化数据】');
  repos.forEach((r, i) => {
    console.log(`\n${i + 1}. ${r.name}`);
    console.log(`   描述: ${r.desc || '(无)'}`);
    console.log(`   语言: ${r.lang}, Stars: ${r.stars}`);
  });

  // 4. 判断页面是否有特定内容
  const hasAI = fullText.toLowerCase().includes('ai');
  const hasPython = fullText.toLowerCase().includes('python');
  console.log(`\n【内容判断】包含 AI 相关: ${hasAI}, 包含 Python: ${hasPython}`);

  // 5. 读 meta 标签
  const description = await page
    .locator('meta[name="description"]')
    .getAttribute('content');
  console.log('【meta description】', description?.slice(0, 80), '...');

  // 6. 获取所有链接
  const links = await page.locator('a[href]').count();
  console.log('【链接总数】', links);

  await browser.close();
  console.log('\n✅ 完成，全程无截图');
})();
