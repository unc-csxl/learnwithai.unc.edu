import { defineConfig } from 'vitest/config';

import { angularComponentResourcesPlugin } from './vitest.angular-component-resources';

const isDirectVitestRun =
  process.env['VITEST_VSCODE'] === 'true' ||
  process.argv.some((arg) => /(^|\/)vitest(?:\.mjs)?$/.test(arg) || arg.includes('/vitest/'));

export default defineConfig({
  plugins: isDirectVitestRun ? [angularComponentResourcesPlugin()] : [],
  test: {
    globals: true,
    environment: 'jsdom',
    exclude: ['dist/**', '.angular/**', 'node_modules/**'],
    setupFiles: isDirectVitestRun ? ['src/test-setup.ts'] : [],
    ...(isDirectVitestRun ? { include: ['src/**/*.spec.ts'] } : {}),
  },
});
