const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const os = require('node:os');
const path = require('node:path');
const { createCipheriv, createDecipheriv, randomBytes } = require('node:crypto');
const { LightingController, defaults, normalizeUrl } = require('./lighting.cjs');

function testStorage() {
  const key = randomBytes(32);
  return {
    isEncryptionAvailable: () => true,
    getSelectedStorageBackend: () => 'gnome_libsecret',
    encryptString: (text) => {
      const iv = randomBytes(12);
      const cipher = createCipheriv('aes-256-gcm', key, iv);
      const encrypted = Buffer.concat([cipher.update(text, 'utf8'), cipher.final()]);
      return Buffer.concat([iv, cipher.getAuthTag(), encrypted]);
    },
    decryptString: (data) => {
      const cipher = createDecipheriv('aes-256-gcm', key, data.subarray(0, 12));
      cipher.setAuthTag(data.subarray(12, 28));
      return Buffer.concat([cipher.update(data.subarray(28)), cipher.final()]).toString('utf8');
    },
  };
}

async function fixture(t, fetchImpl, options = {}) {
  const directory = await fs.mkdtemp(path.join(os.tmpdir(), 'lichtspiel-light-test-'));
  const controller = new LightingController({
    filename: path.join(directory, 'lighting.json'),
    secureStorage: testStorage(),
    fetchImpl,
    ...options,
  });
  t.after(async () => {
    controller.close();
    await fs.rm(directory, { recursive: true, force: true });
  });
  const config = {
    ...defaults(),
    enabled: true,
    baseUrl: 'http://homeassistant.local:8123',
    entityId: 'light.kinosaal',
    token: 'private-test-token',
  };
  return { controller, config };
}

const ok = (data) => ({ ok: true, status: 200, json: async () => data });

test('lighting defaults are disabled and never send on progress or initial idle', async (t) => {
  const { controller } = await fixture(t, () => assert.fail('unexpected request'));
  assert.equal(controller.publicConfig().enabled, false);
  controller.observePlayback({ status: 'idle', index: 0 }, []);
  controller.observePlayback({ status: 'playing', index: 0 }, [{ category: 'Film' }]);
  await controller.queue;
  assert.match(controller.preview('feature').description, /deaktiviert/);
});

test('tokens are encrypted at rest, never exposed, and cannot follow a server change', async (t) => {
  const { controller, config } = await fixture(t, () => assert.fail('unexpected request'));
  await controller.save(config);
  const saved = await fs.readFile(controller.filename, 'utf8');
  assert.ok(!saved.includes(config.token));
  assert.equal(controller.publicConfig().hasToken, true);
  assert.ok(!JSON.stringify(controller.publicConfig()).includes(config.token));
  const restored = new LightingController({
    filename: controller.filename,
    secureStorage: controller.secureStorage,
  });
  await restored.load();
  assert.equal(restored.publicConfig().hasToken, true);
  await assert.rejects(
    () => controller.save({ ...config, token: undefined, baseUrl: 'http://other.local:8123' }),
    /Token/,
  );
  assert.equal(controller.publicConfig().baseUrl, config.baseUrl);
  await controller.save({
    ...config,
    enabled: false,
    token: undefined,
    baseUrl: 'http://other.local:8123',
  });
  assert.equal(controller.publicConfig().hasToken, false);
});

test('no plaintext fallback is permitted for Linux basic_text storage', async (t) => {
  const storage = {
    isEncryptionAvailable: () => true,
    getSelectedStorageBackend: () => 'basic_text',
    encryptString: () => assert.fail('unsafe encryption'),
  };
  const { controller, config } = await fixture(t, () => assert.fail(), {
    secureStorage: storage,
    platform: 'linux',
  });
  assert.equal(controller.publicConfig().available, false);
  await assert.rejects(() => controller.save(config), /Sichere Token-Ablage/);
  await assert.rejects(() => fs.access(controller.filename));
});

test('changing both public origin fields on disk cannot redirect the encrypted token', async (t) => {
  const { controller, config } = await fixture(t, () => assert.fail('unexpected request'));
  await controller.save(config);
  const stored = JSON.parse(await fs.readFile(controller.filename, 'utf8'));
  stored.baseUrl = stored.tokenOrigin = 'https://different.example.test';
  await fs.writeFile(controller.filename, JSON.stringify(stored));
  const restored = new LightingController({
    filename: controller.filename,
    secureStorage: controller.secureStorage,
  });
  await restored.load();
  assert.equal(restored.publicConfig().hasToken, false);
  assert.equal(restored.publicConfig().enabled, false);
});

test('URL validation rejects credentials, paths, query, fragment and unsupported schemes', () => {
  for (const url of [
    'http://user:pass@host',
    'http://host/api/',
    'http://host/?secret=x',
    'http://host/#x',
    'file:///tmp/ha',
  ])
    assert.throws(() => normalizeUrl(url));
  assert.equal(normalizeUrl('http://homeassistant.local:8123/'), 'http://homeassistant.local:8123');
  assert.equal(normalizeUrl('https://ha.example.test'), 'https://ha.example.test');
});

test('connection test is GET-only, follows no redirects, and preview makes no request', async (t) => {
  const calls = [];
  const { controller, config } = await fixture(t, async (url, options) => {
    calls.push({ url, options });
    return ok(
      url.endsWith('/states')
        ? [
            { entity_id: 'light.cinema', attributes: { friendly_name: 'Kino' } },
            { entity_id: 'switch.socket' },
          ]
        : { message: 'API running.' },
    );
  });
  await controller.save(config);
  const result = await controller.testConnection();
  assert.deepEqual(result.lights, [{ id: 'light.cinema', label: 'Kino' }]);
  assert.deepEqual(
    calls.map((call) => call.url),
    [`${config.baseUrl}/api/`, `${config.baseUrl}/api/states`],
  );
  assert.ok(
    calls.every((call) => call.options.method === 'GET' && call.options.redirect === 'error'),
  );
  assert.match(controller.preview('feature').description, /nur eine Vorschau/);
  assert.equal(calls.length, 2);
});

test('manual apply uses light service, correct percentage and zero maps to turn_off', async (t) => {
  const calls = [];
  const { controller, config } = await fixture(t, async (url, options) => {
    calls.push({ url, ...options });
    return ok([]);
  });
  await controller.save(config);
  await controller.apply('preshow');
  await controller.apply('feature');
  assert.equal(calls[0].method, 'POST');
  assert.ok(calls[0].url.endsWith('/light/turn_on'));
  assert.deepEqual(JSON.parse(calls[0].body), {
    entity_id: 'light.kinosaal',
    transition: 3,
    brightness_pct: 20,
  });
  assert.ok(calls[1].url.endsWith('/light/turn_off'));
  assert.deepEqual(JSON.parse(calls[1].body), { entity_id: 'light.kinosaal', transition: 3 });
});

test('automatic rules fire on semantic transitions, not time-pos; errors do not raise lights', async (t) => {
  const calls = [];
  const { controller, config } = await fixture(t, async (_url, options) => {
    calls.push(JSON.parse(options.body));
    return ok([]);
  });
  await controller.save(config);
  const items = [{ category: 'Werbung' }, { category: 'Film' }];
  async function state(status, index = 0, meta) {
    controller.observePlayback({ status, index, position: Math.random() }, items, meta);
    await controller.queue;
  }
  await state('idle');
  await state('playing');
  await state('playing');
  await state('playing');
  assert.equal(calls.length, 1);
  await state('playing', 1);
  await state('paused', 1);
  await state('paused', 1);
  await state('blackout', 1);
  assert.equal(calls.length, 3);
  await state('playing', 1);
  await state('finished', 1);
  await state('idle');
  assert.deepEqual(
    calls.map((call) => call.brightness_pct ?? 0),
    [20, 0, 40, 0, 80],
  );
  await state('playing');
  await state('idle', 0, { reason: 'error' });
  await state('error');
  assert.equal(calls.length, 6);
  await state('playing');
  await state('idle');
  assert.equal(calls.at(-1).brightness_pct, 80);
});

test('requests serialize and request failures do not reject playback observers', async (t) => {
  let active = 0;
  let maximum = 0;
  const notices = [];
  const { controller, config } = await fixture(t, async () => {
    active += 1;
    maximum = Math.max(maximum, active);
    await new Promise((resolve) => setTimeout(resolve, 5));
    active -= 1;
    return ok([]);
  });
  await controller.save(config);
  await Promise.all([
    controller.apply('preshow'),
    controller.apply('pause'),
    controller.apply('end'),
  ]);
  assert.equal(maximum, 1);
  controller.on('notice', (notice) => notices.push(notice));
  controller.fetchImpl = async () => {
    throw new Error(`secret ${config.token}`);
  };
  assert.equal(
    controller.observePlayback({ status: 'playing', index: 0 }, [{ category: 'Film' }]),
    undefined,
  );
  await assert.rejects(controller.queue, /nicht erreichbar/);
  assert.equal(notices.at(-1).status, 'error');
  assert.ok(!JSON.stringify(notices).includes(config.token));
});

test('requests time out and disabled per-event rules send nothing', async (t) => {
  const { controller, config } = await fixture(
    t,
    async (_url, { signal }) =>
      new Promise((_resolve, reject) =>
        signal.addEventListener('abort', () => reject(new Error('abort'))),
      ),
    { timeout: 10 },
  );
  config.rules.pause.enabled = false;
  await controller.save(config);
  assert.match((await controller.apply('pause')).description, /deaktiviert/);
  await assert.rejects(() => controller.apply('preshow'), /nicht rechtzeitig/);
});
