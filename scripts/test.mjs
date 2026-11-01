import { readdir } from 'node:fs/promises';
import { spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const root = fileURLToPath(new URL('../', import.meta.url));
const files = [];
for (const directory of ['electron', 'tests']) {
  const entries = await readdir(path.join(root, directory));
  files.push(
    ...entries
      .filter((name) => /\.test\.(cjs|mjs)$/.test(name))
      .map((name) => path.join(root, directory, name)),
  );
}
if (!files.length) throw new Error('Keine Tests gefunden.');

// Resolve paths ourselves: Windows shells do not expand the same globs as bash.
const child = spawn(process.execPath, ['--test', ...files.sort()], { cwd: root, stdio: 'inherit' });
child.once('error', (error) => {
  console.error(error.message);
  process.exitCode = 1;
});
child.once('exit', (code) => {
  process.exitCode = code ?? 1;
});
