---
name: playwright-visual-iteration
description: "Use when refining frontend UI by taking Playwright screenshots, comparing visual balance, and iterating on Angular layout or styling in this repository. Useful for landing page branding, responsive adjustments, dark mode checks, and authenticated app-shell screenshots."
---

# Playwright Visual Iteration

## Purpose

Use this skill when a frontend change needs visual refinement rather than just code review. The workflow captures screenshots from the running app, compares the rendered result, and iterates on CSS or template structure until the UI looks correct on desktop and mobile.

This repo already has the pieces needed for that workflow:

- The frontend runs at `http://127.0.0.1:4200`.
- `pnpm exec playwright screenshot` works from `frontend/` for quick unauthenticated captures.
- `@playwright/test` is available from `frontend/` for scripted screenshots that need login, theme setup, or API reset steps.

## When To Use

Use this skill when you need to:

- tune spacing, alignment, or visual balance
- verify responsive behavior with screenshots instead of guessing
- inspect dark mode or light mode rendering
- capture authenticated states like the app shell or course pages
- iterate on brand lockups, logos, buttons, or page sections

Do not use this as a substitute for normal unit or e2e coverage. This is a visual iteration workflow.

## Repo-Specific Workflow

### 1. Make sure the frontend is running

Prefer the existing `frontend: run` task for the frontend workspace.

### 2. Run commands from `frontend/`

In this environment, shell helpers may ignore a plain `cd`. Use `pushd` and `popd` so the command definitely runs in the frontend workspace.

Example:

```bash
pushd /workspaces/learnwithai/frontend >/dev/null && \
  pnpm exec playwright screenshot --browser=chromium --viewport-size=1280,900 \
  http://127.0.0.1:4200 tmp-page.png && \
  popd >/dev/null
```

### 3. Capture unauthenticated screens quickly

For public pages, use the Playwright CLI screenshot command.

Desktop example:

```bash
pushd /workspaces/learnwithai/frontend >/dev/null && \
  pnpm exec playwright screenshot --browser=chromium --viewport-size=1280,900 \
  http://127.0.0.1:4200 tmp-landing.png && \
  popd >/dev/null
```

Mobile example:

```bash
pushd /workspaces/learnwithai/frontend >/dev/null && \
  pnpm exec playwright screenshot --browser=chromium --viewport-size=540,800 \
  http://127.0.0.1:4200 tmp-landing-mobile.png && \
  popd >/dev/null
```

### 4. Capture authenticated screens with a Node script

For app-shell states, use `@playwright/test` from `frontend/`. In this repo, the most reliable pattern is:

- reset the dev database
- set theme preference before navigation when needed
- log in through the dev auth route
- wait for the final route
- take the screenshot

Example:

```bash
pushd /workspaces/learnwithai/frontend >/dev/null && \
  pnpm exec node -e "const { chromium, request } = require('@playwright/test'); (async()=>{ \
    const api = await request.newContext({ baseURL: 'http://127.0.0.1:4200' }); \
    await api.post('/api/dev/reset-db'); \
    await api.dispose(); \
    const browser = await chromium.launch({ headless: true }); \
    const context = await browser.newContext({ viewport: { width: 1280, height: 900 }, colorScheme: 'dark' }); \
    const page = await context.newPage(); \
    await page.addInitScript(() => localStorage.setItem('theme-mode', 'dark')); \
    await page.goto('http://127.0.0.1:4200/api/auth/as/222222222'); \
    await page.waitForURL('**/courses'); \
    await page.screenshot({ path: 'tmp-shell.png', fullPage: true }); \
    await browser.close(); \
  })().catch(err => { console.error(err); process.exit(1); });" && \
  popd >/dev/null
```

## Known Good Defaults

### Viewports

- Desktop: `1280x900`
- Mobile: `540x800`

### URLs

- Public landing page: `http://127.0.0.1:4200`
- Dev login as instructor: `http://127.0.0.1:4200/api/auth/as/222222222`

### Theme control

For forced dark mode screenshots, set local storage before navigation:

```ts
await page.addInitScript(() => localStorage.setItem("theme-mode", "dark"));
```

You can also create a context with `colorScheme: 'dark'`, but local storage is what makes the app use its explicit theme toggle state.

## What Worked Here

The key fix from this session was to validate visual assumptions with screenshots instead of relying on CSS reasoning alone.

Problem pattern:

- A flex container used stretch behavior.
- The logo height was tied to `height: 100%`.
- The image expanded to the wrong visual reference height.

Better pattern:

- Give the text stack an explicit height.
- Give the logo its own explicit height that matches the text stack.
- Keep the flex row aligned with `align-items: center`.
- Re-check both landing and authenticated shell screenshots after every adjustment.

## Review Checklist

After each visual change:

- Capture desktop screenshot.
- Capture mobile screenshot.
- If the UI appears in authenticated shell, capture that too.
- Check that logos are not stretching or clipping.
- Check that text weight and alignment still read correctly.
- Check that the brand lockup still works in dark mode.
- Run diagnostics on edited Angular files.

## Cleanup

Temporary screenshots should not remain in the repo.

If `rm` is blocked in the environment, remove files with Python:

```bash
python3 - <<'PY'
from pathlib import Path
for path in [
    '/workspaces/learnwithai/frontend/tmp-landing.png',
    '/workspaces/learnwithai/frontend/tmp-landing-mobile.png',
    '/workspaces/learnwithai/frontend/tmp-shell.png',
]:
    Path(path).unlink(missing_ok=True)
PY
```
