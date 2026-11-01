const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const path = require('node:path');
const os = require('node:os');
const { JsonLines, displayArgs, preflight } = require('./mpv.cjs');
const { ShowScheduler } = require('./scheduler.cjs');

test('JSON IPC handles split messages, multiple messages and non-JSON diagnostics', () => {
  const received = [];
  const parser = new JsonLines((message) => received.push(message));
  parser.push('{"event":"property-');
  parser.push('change","data":12}\nnot JSON\n{"request_id":3,"error":"success"}\n');
  assert.deepEqual(received, [
    { event: 'property-change', data: 12 },
    { request_id: 3, error: 'success' },
  ]);
});

test('projection test and playback use the same display selection', () => {
  assert.deepEqual(displayArgs(2), ['--screen=2', '--fs-screen=2']);
  assert.throws(() => displayArgs(-1), /Ausgabebildschirm/);
});

test('scheduler fires once at the chosen time', async () => {
  let now = 1000;
  const starts = [];
  const scheduler = new ShowScheduler({
    now: () => now,
    start: async (show) => starts.push(show),
    isBusy: () => false,
    onError: assert.fail,
  });
  scheduler.arm({ at: new Date(2000).toISOString(), items: ['test'] });
  await scheduler.tick();
  assert.equal(starts.length, 0);
  now = 2001;
  await Promise.all([scheduler.tick(), scheduler.tick()]);
  assert.equal(starts.length, 1);
});

test('scheduler never starts late after sleep and never interrupts another show', async () => {
  let now = 1000;
  let busy = false;
  const errors = [];
  const scheduler = new ShowScheduler({
    now: () => now,
    start: assert.fail,
    isBusy: () => busy,
    onError: (message) => errors.push(message),
  });
  scheduler.arm({ at: new Date(2000).toISOString() });
  now = 50000;
  await scheduler.tick();
  assert.match(errors[0], /nicht bereit/);
  scheduler.arm({ at: new Date(51000).toISOString() });
  now = 51000;
  busy = true;
  await scheduler.tick();
  assert.match(errors[1], /bereits/);
  assert.equal(scheduler.pending, null);
});

test('scheduler cancellation and invalid dates', async () => {
  const scheduler = new ShowScheduler({
    now: () => 1000,
    start: assert.fail,
    isBusy: () => false,
    onError: assert.fail,
  });
  assert.throws(() => scheduler.arm({ at: 'invalid' }), /Zukunft/);
  assert.throws(() => scheduler.arm({ at: new Date(999).toISOString() }), /Zukunft/);
  scheduler.arm({ at: new Date(2000).toISOString() });
  scheduler.arm(null);
  await scheduler.tick();
  assert.equal(scheduler.pending, null);
});

test('preflight rejects missing files and accepts an existing nonempty local file', async () => {
  const directory = await fs.mkdtemp(path.join(os.tmpdir(), 'lichtspiel-test-'));
  try {
    const filename = path.join(directory, 'sample.mp4');
    await fs.writeFile(filename, 'test');
    await preflight([{ path: filename, duration: 120 }]);
    await assert.rejects(
      () => preflight([{ path: path.join(directory, 'missing.mp4'), duration: 120 }]),
      /fehlt/,
    );
    await assert.rejects(
      () => preflight([{ path: 'https://example.com/video.mp4', duration: 120 }]),
      /ungültige/,
    );
    await assert.rejects(() => preflight([{ path: filename, duration: 0 }]), /Laufzeit/);
    await assert.rejects(() => preflight([]), /Medien/);
  } finally {
    await fs.rm(directory, { recursive: true });
  }
});
