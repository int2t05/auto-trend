const { defineConfig, devices } = require('@playwright/test');
const dotenv = require('dotenv');
const path = require('path');

// 加载项目根目录的 .env
dotenv.config({ path: path.resolve(__dirname, '.env') });

const GITHUB_PAGES_URL =
  process.env.PLAYWRIGHT_BASE_URL ||
  'https://int2t05.github.io/auto-trend/';

const GITHUB_URL = 'https://github.com';

module.exports = defineConfig({
  testDir: './e2e/tests',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 2 : undefined,
  reporter: [
    ['html', { open: 'never' }],
    ['list'],
  ],

  timeout: 30_000,
  expect: { timeout: 10_000 },

  use: {
    locale: 'zh-CN',
    timezoneId: 'Asia/Shanghai',

    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',

    userAgent:
      'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
  },

  projects: [
    // === GitHub Pages (发布的日报) ===
    {
      name: 'pages-desktop',
      testMatch: '**/pages/**/*.spec.js',
      use: {
        ...devices['Desktop Chrome'],
        baseURL: GITHUB_PAGES_URL,
        viewport: { width: 1440, height: 900 },
      },
    },
    {
      name: 'pages-mobile',
      testMatch: '**/pages/**/*.spec.js',
      use: {
        ...devices['iPhone 14'],
        baseURL: GITHUB_PAGES_URL,
      },
    },

    // === GitHub Trending (数据源) ===
    {
      name: 'trending-desktop',
      testMatch: '**/trending/**/*.spec.js',
      use: {
        ...devices['Desktop Chrome'],
        baseURL: GITHUB_URL,
        viewport: { width: 1440, height: 900 },
      },
    },
  ],
});
