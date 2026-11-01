const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const os = require('node:os');
const path = require('node:path');
const { checkShowReadiness } = require('./readiness.cjs');

test('start check reports readable media, a working player and selected display', async () => {
  const directory = await fs.mkdtemp(path.join(os.tmpdir(), 'lichtspiel-ready-'));
  try {
    const filename = path.join(directory, 'film.mp4');
    await fs.writeFile(filename, 'video');
    const result = await checkShowReadiness(
      { items: [{ path: filename, duration: 120 }], displayId: 'beamer' },
      {
        displayList: [{ id: 'beamer', label: 'Saalbeamer' }],
        mpvPath: '/test/mpv',
        checkPlayer: async () => true,
      },
    );
    assert.equal(result.ready, true);
    assert.deepEqual(
      result.checks.map((check) => check.ok),
      [true, true, true],
    );
    assert.equal(result.checks[2].message, 'Saalbeamer');
  } finally {
    await fs.rm(directory, { recursive: true });
  }
});

test('start check explains missing media, player and disconnected output separately', async () => {
  const result = await checkShowReadiness(
    {
      items: [{ path: path.join(os.tmpdir(), 'missing-lichtspiel.mp4'), duration: 120 }],
      displayId: 'gone',
    },
    { displayList: [], mpvPath: '', checkPlayer: async () => false },
  );
  assert.equal(result.ready, false);
  assert.deepEqual(
    result.checks.map((check) => check.ok),
    [false, false, false],
  );
  assert.match(result.checks[0].message, /fehlt oder ist nicht lesbar/);
  assert.match(result.checks[1].message, /mpv/);
  assert.match(result.checks[2].message, /Bildschirm/);
});

test('start check rejects a corrupted media duration before playback', async () => {
  const directory = await fs.mkdtemp(path.join(os.tmpdir(), 'lichtspiel-duration-'));
  try {
    const filename = path.join(directory, 'film.mp4');
    await fs.writeFile(filename, 'video');
    const result = await checkShowReadiness(
      { items: [{ path: filename, duration: 0 }], displayId: 'beamer' },
      {
        displayList: [{ id: 'beamer', label: 'Saalbeamer' }],
        mpvPath: '/test/mpv',
        checkPlayer: async () => true,
      },
    );
    assert.equal(result.ready, false);
    assert.match(result.checks[0].message, /Laufzeit/);
  } finally {
    await fs.rm(directory, { recursive: true });
  }
});
