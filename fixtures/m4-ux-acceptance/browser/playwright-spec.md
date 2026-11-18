# Playwright acceptance scaffold — M4-B (unexecuted)

This file is a **test specification**, not a report. It has not been run. Codex
should copy the TypeScript block into the M4 web test suite, replace only the
`SELECTORS` map with real contracts, and keep every assertion intact.

```ts
// m4-ux-acceptance.spec.ts — Playwright + @axe-core/playwright
import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

/**
 * Codex: replace these values with the frozen UI contract. Do not change the
 * assertions below to accommodate a mismatch; report the mismatch as a defect.
 */
const SELECTORS = {
  sampleButton: { role: 'button', name: /try a sample/i },
  compareButton: { role: 'button', name: /compare behavior/i },
  retryButton: { role: 'button', name: /retry/i },
  resetButton: { role: 'button', name: /reset project/i },
  exportLink: { role: 'link', name: /download .*evidence/i },
  resultRegion: { role: 'region', name: /comparison result/i },
  statusRegion: { role: 'region', name: /status/i },
  preflightRegion: { role: 'region', name: /pre-flight/i },
  witnessTable: { role: 'table', name: /counterexample/i },
  pinTable: { role: 'table', name: /pin mapping/i },
  processorInput: { role: 'textbox', name: /processor address/i },
  circuitIdInput: { role: 'textbox', name: /circuit id/i },
} as const;

const loc = (page: any, key: keyof typeof SELECTORS) =>
  page.getByRole(SELECTORS[key].role as any, { name: SELECTORS[key].name });

async function expectNoAxeViolations(page: any) {
  const results = await new AxeBuilder({ page }).analyze();
  expect(results.violations, JSON.stringify(results.violations, null, 2)).toEqual([]);
}

// B01 — keyboard-only operation
test('B01 sample journey is keyboard operable', async ({ page }) => {
  await page.goto('/');
  await page.keyboard.press('Tab');
  await expect(loc(page, 'sampleButton')).toBeVisible();
  await loc(page, 'sampleButton').focus();
  await page.keyboard.press('Enter');
  await loc(page, 'compareButton').focus();
  await page.keyboard.press('Enter');
  await expect(loc(page, 'resultRegion')).toContainText(/different/i);
  await expect(loc(page, 'exportLink')).toBeVisible();
  await expectNoAxeViolations(page);
});

// B02 — focus order and visibility
test('B02 error state moves focus and keeps a visible indicator', async ({ page }) => {
  await page.goto('/');
  await loc(page, 'processorInput').fill('0x839bdd6fa7a66416a609a735e11de5411b98574e');
  await loc(page, 'circuitIdInput').fill('1');
  await page.getByRole('button', { name: /import/i }).click();
  await expect(loc(page, 'statusRegion')).toContainText(/wrong network|unavailable/i);
  const focused = await page.evaluate(() => {
    const el = document.activeElement as HTMLElement;
    return { tag: el.tagName, outline: getComputedStyle(el).outlineStyle };
  });
  expect(focused.outline).not.toBe('none');
});

// B03 — accessible labels
test('B03 every control has a name and pin indices are exposed', async ({ page }) => {
  await page.goto('/');
  await loc(page, 'sampleButton').click();
  const unnamed = await page.evaluate(() =>
    Array.from(document.querySelectorAll('button,input,select'))
      .filter((el) => !(el as HTMLElement).getAttribute('aria-label') &&
        !el.textContent?.trim() && !el.getAttribute('title'))
      .map((el) => el.outerHTML)
  );
  expect(unnamed).toEqual([]);
  await expect(loc(page, 'pinTable')).toContainText(/width|pin/i);
});

// B04 — screen-reader-friendly announcements (text assertions; manual SR pass required)
test('B04 verdict and freshness are announced separately as text', async ({ page }) => {
  await page.goto('/');
  await loc(page, 'sampleButton').click();
  await loc(page, 'compareButton').click();
  const status = await loc(page, 'statusRegion').textContent();
  expect(status).toMatch(/DIFFERENT|EQUIVALENT/);
  expect(status).toMatch(/HISTORICAL/);
  await expect(loc(page, 'witnessTable')).toBeVisible();
  await expect(loc(page, 'witnessTable')).toContainText(/reference/i);
  await expect(loc(page, 'witnessTable')).toContainText(/candidate/i);
});

// B05 — responsive layout
for (const width of [320, 768, 1280]) {
  test(`B05 no lost function at ${width}px`, async ({ page }) => {
    await page.setViewportSize({ width, height: 800 });
    await page.goto('/');
    await loc(page, 'sampleButton').click();
    await loc(page, 'compareButton').click();
    await expect(loc(page, 'resultRegion')).toBeVisible();
    const overflow = await page.evaluate(() =>
      document.documentElement.scrollWidth > document.documentElement.clientWidth
    );
    expect(overflow).toBe(false);
  });
}

// B06 — loading and error states
test('B06 failure preserves project text and exposes technical details', async ({ page }) => {
  await page.goto('/');
  await loc(page, 'processorInput').fill('0x839bdd6fa7a66416a609a735e11de5411b98574e');
  await page.getByRole('button', { name: /import/i }).click();
  await expect(loc(page, 'statusRegion')).toContainText(/could not|wrong network/i);
  await expect(loc(page, 'statusRegion')).toContainText(/technical details/i);
  await expect(loc(page, 'processorInput')).toHaveValue(
    '0x839bdd6fa7a66416a609a735e11de5411b98574e'
  );
});

// B07 — timeout
test('B07 timeout is UNKNOWN and never EQUIVALENT', async ({ page }) => {
  await page.goto('/');
  await loc(page, 'sampleButton').click();
  await page.getByRole('button', { name: /use 1 ms deadline/i }).click();
  await loc(page, 'compareButton').click();
  await expect(loc(page, 'statusRegion')).toContainText(/inconclusive/i);
  await expect(loc(page, 'statusRegion')).toContainText(/UNKNOWN/);
  await expect(loc(page, 'resultRegion')).not.toContainText(/circuits are equivalent/i);
  await expect(loc(page, 'retryButton')).toBeVisible();
});

// B08 — repeated workflow
test('B08 five runs produce identical digest and verdict', async ({ page }) => {
  await page.goto('/');
  await loc(page, 'sampleButton').click();
  const seen = new Set<string>();
  for (let i = 0; i < 5; i++) {
    await loc(page, 'compareButton').click();
    seen.add((await loc(page, 'resultRegion').textContent()) ?? '');
  }
  expect(seen.size).toBe(1);
});

// B09 — refresh and recovery
test('B09 unsaved work survives refresh; reset needs confirmation', async ({ page }) => {
  await page.goto('/');
  await loc(page, 'processorInput').fill('0x839bdd6fa7a66416a609a735e11de5411b98574e');
  await page.reload();
  await expect(loc(page, 'processorInput')).toHaveValue(
    '0x839bdd6fa7a66416a609a735e11de5411b98574e'
  );
  await expect(page.getByText(/restored/i)).toBeVisible();
  await loc(page, 'resetButton').click();
  await expect(page.getByRole('dialog')).toContainText(/confirm/i);
});

// B10 — export accessibility
test('B10 export link is named and summary is structured', async ({ page }) => {
  await page.goto('/');
  await loc(page, 'sampleButton').click();
  await loc(page, 'compareButton').click();
  await expect(loc(page, 'exportLink')).toHaveAttribute('download', /.*/);
  const headings = await page.locator('h1,h2,h3').count();
  expect(headings).toBeGreaterThan(0);
});

// B11 — pre-flight status separation
test('B11 preflight UNKNOWN is not styled as success', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('button', { name: /run read-only pre-flight/i }).click();
  await expect(loc(page, 'preflightRegion')).toContainText(/UNKNOWN/i);
  await expect(loc(page, 'preflightRegion')).toContainText(/no transaction/i);
  await expect(loc(page, 'preflightRegion')).not.toContainText(/EQUIVALENT/);
  expect(await page.getByRole('button', { name: /sign|broadcast/i }).count()).toBe(0);
});
```

## Notes for integration

- B04 and B10 additionally need a **manual** screen-reader pass (NVDA/VoiceOver):
  confirm the live region announces verdict and freshness as separate statements,
  and that the witness table is navigable by cell with headers announced.
- CLI correlates are listed in `accessibility-matrix.json`; a browser scenario
  that contradicts its CLI correlate is a defect, not a UI preference.
- The 1 ms deadline control in B07 is a test-only affordance; production may
  expose a budget selector whose smallest allowed value is 1 ms.
- Nothing in this scaffold has been executed on the M3 baseline.
