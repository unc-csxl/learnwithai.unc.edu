import { defineConfig } from 'vitest/config';

const isDirectVitestRun =
  process.env['VITEST_VSCODE'] === 'true' ||
  process.argv.some((arg) => /(^|\/)vitest(?:\.mjs)?$/.test(arg) || arg.includes('/vitest/'));

export default defineConfig({
  test: {
    globals: true,
    environment: 'jsdom',
    exclude: ['dist/**', '.angular/**', 'node_modules/**'],
    include: isDirectVitestRun ? ['src/**/*.spec.ts'] : undefined,
    setupFiles: isDirectVitestRun ? ['src/test-setup.ts'] : [],
  },
});
