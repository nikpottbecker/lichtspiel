import { mkdirSync } from 'node:fs';
import path from 'node:path';
import { chromium } from '@playwright/test';
import assert from 'node:assert/strict';

const artifacts = process.env.LICHTSPIEL_TEST_ARTIFACTS || 'design';
mkdirSync(artifacts, { recursive: true });

// Frontend contract test. The desktop bridge is simulated; no network/device call.
const browser = await chromium.launch({ headless: true, args: ['--no-sandbox'] });
try {
  const context = await browser.newContext({ viewport: { width: 1440, height: 1000 } });
  await context.addInitScript(() => {
    let lighting = {
      enabled: false,
      baseUrl: '',
      entityId: '',
      hasToken: false,
      available: true,
      rules: Object.fromEntries(
        ['preshow', 'feature', 'pause', 'end'].map((event, i) => [
          event,
          { enabled: true, brightness: [20, 0, 40, 80][i], transition: 3 },
        ]),
      ),
    };
    window.calls = { reads: 0, writes: 0 };
    window.cinema = {
      getEnvironment: async () => ({
        desktop: true,
        platform: 'darwin',
        displays: [
          { id: 'external', label: 'Testbeamer', width: 1920, height: 1080, primary: false },
        ],
        mpvAvailable: true,
        mpvPath: '/test/mpv',
      }),
      loadProject: async () => ({
        version: 1,
        title: 'Filmabend',
        library: [],
        queue: [],
        displayId: 'external',
        audioDevice: 'auto',
        onboarded: true,
        startAt: '',
      }),
      saveProject: async () => {},
      onPlayback: () => () => {},
      onLighting: () => () => {},
      getLighting: async () => structuredClone(lighting),
      saveLighting: async (input) => {
        const { token, ...config } = input;
        lighting = { ...config, hasToken: !!token || lighting.hasToken };
        return structuredClone(lighting);
      },
      testLightingConnection: async () => {
        window.calls.reads++;
        return {
          message: 'Verbindung hergestellt.',
          lights: [{ id: 'light.kino', label: 'Kinolichter' }],
        };
      },
      previewLighting: async () => ({ description: 'Vorschau ohne Gerätebefehl.' }),
      applyLighting: async () => {
        window.calls.writes++;
      },
    };
  });
  const page = await context.newPage();
  await page.goto('http://localhost:5173');
  await page.getByRole('button', { name: 'Lichtsteuerung', exact: true }).click();
  await page.getByLabel('Home-Assistant-Adresse').fill('http://homeassistant.local:8123');
  await page.getByLabel('Zugriffstoken').fill('mock-token-for-ui-test');
  await page.getByRole('button', { name: 'Speichern', exact: true }).click();
  assert.equal(await page.getByLabel('Zugriffstoken').inputValue(), '');
  await page.getByRole('button', { name: 'Verbindung prüfen', exact: true }).click();
  await page.getByLabel('Licht oder Lichtgruppe').selectOption('light.kino');
  await page.getByRole('switch', { name: 'Automatisch steuern' }).check();
  await page.getByRole('button', { name: 'Speichern', exact: true }).click();
  await page.getByRole('button', { name: 'Vorschau', exact: true }).nth(1).click();
  assert.deepEqual(await page.evaluate(() => window.calls), { reads: 1, writes: 0 });
  await page.getByRole('button', { name: 'Licht jetzt testen', exact: true }).nth(1).click();
  assert.deepEqual(await page.evaluate(() => window.calls), { reads: 1, writes: 1 });
  assert.equal(
    await page.evaluate(() => Object.values(localStorage).some((v) => v.includes('mock-token'))),
    false,
  );
  await page.screenshot({ path: path.join(artifacts, 'lighting-desktop.png'), fullPage: true });
  const plainContext = await browser.newContext();
  await plainContext.addInitScript(() =>
    localStorage.setItem('lichtspiel-project', 'broken-data-do-not-overwrite'),
  );
  const corrupt = await plainContext.newPage();
  await corrupt.goto('http://localhost:5173');
  await corrupt.getByRole('alert').waitFor();
  await corrupt.waitForTimeout(500);
  assert.equal(
    await corrupt.evaluate(() => localStorage.getItem('lichtspiel-project')),
    'broken-data-do-not-overwrite',
  );
  console.log(
    'PASS: desktop lighting UI contract, credential clearing, save/read/select/activate, dry vs live test separation, no token in localStorage; corrupt project not overwritten. No physical devices contacted.',
  );
} finally {
  await browser.close();
}
