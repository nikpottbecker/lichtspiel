import { mkdirSync } from 'node:fs';
import { chromium } from '@playwright/test';
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { tmpdir } from 'node:os';
import path from 'node:path';
const fixture = path.join(tmpdir(), 'lichtspiel-test.webm');

const artifacts = process.env.LICHTSPIEL_TEST_ARTIFACTS || 'design';
mkdirSync(artifacts, { recursive: true });

// Requires the development server: npm run dev:web
execFileSync('ffmpeg', [
  '-y',
  '-f',
  'lavfi',
  '-i',
  'testsrc2=size=320x180:rate=24',
  '-f',
  'lavfi',
  '-i',
  'sine=frequency=440:sample_rate=48000',
  '-t',
  '4',
  '-c:v',
  'libvpx',
  '-b:v',
  '250k',
  '-c:a',
  'libvorbis',
  fixture,
  '-loglevel',
  'error',
]);
const browser = await chromium.launch({ headless: true, args: ['--no-sandbox'] });
const context = await browser.newContext({ viewport: { width: 1536, height: 1060 } });
const page = await context.newPage();
const errors = [];
page.on('pageerror', (error) => errors.push(error.message));
try {
  await page.goto('http://localhost:5173');
  await page.getByRole('button', { name: 'Weiter', exact: true }).click();
  await page.getByLabel('Vorschau-Ausgabe').selectOption('browser');
  await page.getByRole('button', { name: 'Weiter', exact: true }).click();
  await page.getByRole('button', { name: 'Zur Vorstellung', exact: true }).click();
  await page.getByRole('button', { name: 'Beispielablauf ansehen' }).click();
  await page.getByRole('button', { name: 'Hinweis schließen' }).click();
  await page.getByText('Lokal gespeichert', { exact: true }).waitFor();
  await page.evaluate(() => document.fonts.ready);
  await page.screenshot({ path: path.join(artifacts, 'implementation.png'), fullPage: true });
  await page.getByRole('button', { name: 'Vorstellung starten', exact: true }).click();
  assert.match(await page.getByRole('alert').textContent(), /Beispielablauf/);
  await page.getByRole('button', { name: 'Hinweis schließen' }).click();
  await page.getByRole('button', { name: 'Kinotrailer nach oben' }).click();
  assert.match(await page.locator('.cue-row').first().textContent(), /Kinotrailer/);
  await page.waitForTimeout(500);
  await page.reload();
  await page.locator('.cue-row').first().waitFor();
  assert.match(await page.locator('.cue-row').first().textContent(), /Kinotrailer/);
  await page.setViewportSize({ width: 390, height: 844 });
  assert.equal(
    await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth),
    false,
  );
  await page.screenshot({ path: path.join(artifacts, 'mobile.png'), fullPage: true });
  await page.setViewportSize({ width: 1536, height: 1060 });
  for (const name of ['Willkommen', 'Kinotrailer', 'Hauptfilm'])
    await page.getByRole('button', { name: `${name} aus Ablauf entfernen`, exact: true }).click();
  const chooser = page.waitForEvent('filechooser');
  await page.getByRole('button', { name: 'Medien hinzufügen', exact: true }).click();
  await (await chooser).setFiles(fixture);
  await page.getByText('1 Datei importiert und zum Ablauf hinzugefügt.').waitFor();
  await page.waitForTimeout(400);
  await page.reload();
  await page.getByRole('button', { name: 'Vorstellung starten', exact: true }).waitFor();
  const popupPromise = page.waitForEvent('popup');
  await page.getByRole('button', { name: 'Vorstellung starten', exact: true }).click();
  const popup = await popupPromise;
  await popup.getByRole('button', { name: 'Wiedergabe freigeben' }).click();
  await page.getByRole('button', { name: 'Pause', exact: true }).waitFor();
  await page.getByRole('button', { name: 'Pause', exact: true }).click();
  assert.equal(await popup.locator('video').evaluate((video) => video.paused), true);
  await page.getByRole('button', { name: 'Schwarzbild', exact: true }).click();
  assert.equal(
    await popup.locator('video').evaluate((video) => getComputedStyle(video).visibility),
    'hidden',
  );
  await page.getByRole('button', { name: 'Fortsetzen', exact: true }).click();
  assert.equal(
    await popup.locator('video').evaluate((video) => getComputedStyle(video).visibility),
    'visible',
  );
  await page.getByRole('button', { name: 'Nächster Clip', exact: true }).click();
  await page.getByText('Vorstellung beendet', { exact: true }).waitFor();
  await page.getByRole('button', { name: 'Mediathek', exact: true }).click();
  await page.getByPlaceholder('Medien durchsuchen').fill('lichtspiel');
  assert.equal(await page.locator('.library-row').count(), 1);
  await page.getByRole('button', { name: 'Lichtsteuerung', exact: true }).click();
  await page.getByRole('switch', { name: 'Automatisch steuern' }).check();
  await page.getByRole('button', { name: 'Vorschau', exact: true }).nth(1).click();
  assert.match(await page.locator('.lighting-rule-preview').innerText(), /Hauptfilm.*0 %/);
  await page.screenshot({ path: path.join(artifacts, 'lighting.png'), fullPage: true });
  await page.setViewportSize({ width: 390, height: 844 });
  assert.equal(
    await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth),
    false,
  );
  await page.screenshot({ path: path.join(artifacts, 'lighting-mobile.png'), fullPage: true });
  assert.deepEqual(errors, []);
  console.log(
    'PASS: onboarding, demo refusal, reorder, persistence, mobile layout, video import/restore, actual popup playback, pause, blackout, resume, end, library search, light-rule dry preview and responsive layout.',
  );
} catch (error) {
  console.log('PAGE:', await page.locator('body').innerText());
  console.log('ERRORS:', errors);
  for (const p of context.pages())
    console.log('WINDOW', p.url(), await p.locator('body').innerText());
  throw error;
} finally {
  await browser.close();
}
