import { spawn } from 'node:child_process';
import { mkdir } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const root = fileURLToPath(new URL('../', import.meta.url));
const url = 'http://localhost:5173';
const output = path.resolve(root, process.env.LICHTSPIEL_TEST_ARTIFACTS || 'test-results');
let server;

async function isReady() {
  try {
    const response = await fetch(url, { signal: AbortSignal.timeout(1000) });
    return response.ok && (await response.text()).includes('Lichtspiel');
  } catch {
    return false;
  }
}

async function run(filename) {
  return new Promise((resolve, reject) => {
    const child = spawn(process.execPath, [path.join(root, filename)], {
      cwd: root,
      stdio: 'inherit',
      env: { ...process.env, LICHTSPIEL_TEST_ARTIFACTS: output },
    });
    const timer = setTimeout(() => {
      child.kill();
      reject(new Error(`${filename}: Zeitlimit überschritten.`));
    }, 180000);
    child.once('error', (error) => {
      clearTimeout(timer);
      reject(error);
    });
    child.once('exit', (code) => {
      clearTimeout(timer);
      code === 0 ? resolve() : reject(new Error(`${filename} ist fehlgeschlagen (Exit ${code}).`));
    });
  });
}

try {
  await mkdir(output, { recursive: true });
  if (!(await isReady())) {
    server = spawn(
      process.execPath,
      [
        path.join(root, 'node_modules/vite/bin/vite.js'),
        '--host',
        '127.0.0.1',
        '--port',
        '5173',
        '--strictPort',
      ],
      { cwd: root, stdio: 'inherit' },
    );
    let startupError;
    server.once('error', (error) => {
      startupError = error;
    });
    const deadline = Date.now() + 20000;
    while (!(await isReady())) {
      if (startupError) throw startupError;
      if (server.exitCode !== null)
        throw new Error('Der Testserver konnte nicht starten. Prüfe, ob Port 5173 belegt ist.');
      if (Date.now() > deadline) throw new Error('Der Testserver antwortet nicht.');
      await new Promise((resolve) => setTimeout(resolve, 150));
    }
  }
  await run('tests/browser.mjs');
  await run('tests/lighting-ui.mjs');
} catch (error) {
  console.error(error.message);
  process.exitCode = 1;
} finally {
  server?.kill();
}
