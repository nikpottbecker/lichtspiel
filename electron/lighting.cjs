const { EventEmitter } = require('node:events');
const fs = require('node:fs/promises');
const path = require('node:path');
const { randomUUID } = require('node:crypto');

const EVENTS = ['preshow', 'feature', 'pause', 'end'];
const LABELS = { preshow: 'Vorprogramm', feature: 'Hauptfilm', pause: 'Pause', end: 'Ende' };
const defaults = () => ({
  enabled: false,
  baseUrl: '',
  entityId: '',
  rules: Object.fromEntries(
    Object.entries({ preshow: 20, feature: 0, pause: 40, end: 80 }).map(([event, brightness]) => [
      event,
      { enabled: true, brightness, transition: 3 },
    ]),
  ),
});

function normalizeUrl(value) {
  if (typeof value !== 'string' || !value.trim()) return '';
  let url;
  try {
    url = new URL(value.trim());
  } catch {
    throw new Error('Gib eine vollständige Home-Assistant-Adresse mit http:// oder https:// ein.');
  }
  if (
    !['http:', 'https:'].includes(url.protocol) ||
    url.username ||
    url.password ||
    url.search ||
    url.hash ||
    (url.pathname && url.pathname !== '/')
  ) {
    throw new Error(
      'Nutze nur die Home-Assistant-Basisadresse ohne Zugangsdaten, /api, Suchparameter oder Fragment.',
    );
  }
  return url.origin;
}

function normalizeConfig(input) {
  if (!input || typeof input !== 'object') throw new Error('Ungültige Lichteinstellungen.');
  const config = defaults();
  config.enabled = input.enabled === true;
  config.baseUrl = normalizeUrl(input.baseUrl);
  config.entityId = typeof input.entityId === 'string' ? input.entityId.trim() : '';
  if (config.entityId && !/^light\.[a-z0-9_]+$/.test(config.entityId))
    throw new Error('Wähle eine Licht-Entität wie light.kinosaal.');
  for (const event of EVENTS) {
    const rule = input.rules?.[event] || config.rules[event];
    if (
      typeof rule.brightness !== 'number' ||
      !Number.isFinite(rule.brightness) ||
      rule.brightness < 0 ||
      rule.brightness > 100 ||
      typeof rule.transition !== 'number' ||
      !Number.isFinite(rule.transition) ||
      rule.transition < 0 ||
      rule.transition > 120
    ) {
      throw new Error(
        'Helligkeit muss zwischen 0 und 100 %, Übergang zwischen 0 und 120 Sekunden liegen.',
      );
    }
    config.rules[event] = {
      enabled: rule.enabled === true,
      brightness: Math.round(rule.brightness),
      transition: rule.transition,
    };
  }
  if (config.enabled && (!config.baseUrl || !config.entityId))
    throw new Error('Wähle zuerst Home-Assistant-Adresse und Licht-Entität.');
  return config;
}

class LightingController extends EventEmitter {
  constructor({
    filename,
    secureStorage,
    fetchImpl = globalThis.fetch,
    platform = process.platform,
    timeout = 4000,
  }) {
    super();
    Object.assign(this, { filename, secureStorage, fetchImpl, platform, timeout });
    this.config = defaults();
    this.encryptedToken = '';
    this.tokenOrigin = '';
    this.token = '';
    this.revision = 0;
    this.autoTicket = 0;
    this.queue = Promise.resolve();
    this.saveQueue = Promise.resolve();
    this.previous = { status: 'idle', index: 0, category: undefined };
    this.aborters = new Set();
  }
  available() {
    try {
      if (!this.secureStorage?.isEncryptionAvailable()) return false;
      if (this.platform === 'linux') {
        const backend = this.secureStorage.getSelectedStorageBackend?.();
        if (!backend || backend === 'basic_text') return false;
      }
      return true;
    } catch {
      return false;
    }
  }
  publicConfig() {
    return {
      ...structuredClone(this.config),
      hasToken: !!this.token && this.tokenOrigin === this.config.baseUrl,
      available: this.available(),
    };
  }
  notify(status, message) {
    this.emit('notice', { status, message });
  }
  async load() {
    let stored;
    try {
      stored = JSON.parse(await fs.readFile(this.filename, 'utf8'));
    } catch (error) {
      if (error.code !== 'ENOENT')
        this.notify(
          'error',
          'Lichteinstellungen konnten nicht gelesen werden. Bitte neu einrichten.',
        );
      return this.publicConfig();
    }
    try {
      this.config = normalizeConfig(stored);
      if (typeof stored.encryptedToken === 'string' && stored.tokenOrigin === this.config.baseUrl) {
        this.encryptedToken = stored.encryptedToken;
        this.tokenOrigin = stored.tokenOrigin;
        if (this.encryptedToken && this.available()) {
          const secret = JSON.parse(
            this.secureStorage.decryptString(Buffer.from(this.encryptedToken, 'base64')),
          );
          if (typeof secret.token !== 'string' || secret.origin !== this.config.baseUrl)
            throw new Error('Origin mismatch');
          this.token = secret.token;
        }
      }
    } catch {
      this.config.enabled = false;
      this.token = '';
      this.notify(
        'error',
        'Gespeicherte Licht-Zugangsdaten konnten nicht geöffnet werden. Bitte Token erneut eingeben.',
      );
    }
    return this.publicConfig();
  }
  save(input) {
    const save = this.saveQueue.catch(() => {}).then(() => this.saveNow(input));
    this.saveQueue = save;
    return save;
  }
  async saveNow(input) {
    const config = normalizeConfig(input);
    const supplied = typeof input.token === 'string' ? input.token.trim() : undefined;
    if (supplied && (supplied.length > 8192 || /\s/.test(supplied)))
      throw new Error('Der Token enthält ungültige Zeichen oder ist zu lang.');
    if (supplied && !config.baseUrl) throw new Error('Gib zuerst die Home-Assistant-Adresse ein.');
    let token = this.token;
    let encryptedToken = this.encryptedToken;
    let tokenOrigin = this.tokenOrigin;
    if (config.baseUrl !== tokenOrigin) {
      token = '';
      encryptedToken = '';
      tokenOrigin = '';
    }
    if (supplied !== undefined && supplied !== '') {
      if (!this.available())
        throw new Error(
          'Sichere Token-Ablage ist nicht verfügbar. Aktiviere den macOS-Schlüsselbund, Windows-Anmeldedatenschutz oder unter Linux einen Schlüsselbund und starte die App neu.',
        );
      // Bind the destination inside the encrypted payload as well as in public config.
      try {
        encryptedToken = this.secureStorage
          .encryptString(JSON.stringify({ token: supplied, origin: config.baseUrl }))
          .toString('base64');
      } catch {
        throw new Error(
          'Der Token konnte nicht sicher gespeichert werden. Bitte den System-Schlüsselbund entsperren.',
        );
      }
      token = supplied;
      tokenOrigin = config.baseUrl;
    }
    if (config.enabled && (!this.available() || !token || tokenOrigin !== config.baseUrl))
      throw new Error(
        'Für diesen Home-Assistant-Server wird ein sicher gespeicherter Token benötigt. Bitte neu eingeben.',
      );
    const stored = { ...config, encryptedToken, tokenOrigin };
    await fs.mkdir(path.dirname(this.filename), { recursive: true });
    const temporary = `${this.filename}.${randomUUID()}.tmp`;
    await fs.writeFile(temporary, JSON.stringify(stored, null, 2), { mode: 0o600 });
    await fs.rename(temporary, this.filename);
    this.revision += 1;
    this.autoTicket += 1;
    // Disabling/changing a target cancels requests that have not yet completed.
    for (const aborter of this.aborters) aborter.abort();
    this.config = config;
    Object.assign(this, { token, encryptedToken, tokenOrigin });
    return this.publicConfig();
  }
  requireConnection() {
    if (!this.config.baseUrl || !this.token || this.tokenOrigin !== this.config.baseUrl)
      throw new Error('Speichere zuerst Home-Assistant-Adresse und Token.');
    if (!this.available())
      throw new Error(
        'Die sichere Token-Ablage ist nicht verfügbar. Bitte den System-Schlüsselbund prüfen.',
      );
  }
  async request(endpoint, { method = 'GET', body } = {}) {
    this.requireConnection();
    const base = this.config.baseUrl;
    const target = new URL(endpoint, `${base}/`);
    if (target.origin !== base || !target.pathname.startsWith('/api/'))
      throw new Error('Nicht erlaubte Home-Assistant-Anfrage.');
    const controller = new AbortController();
    this.aborters.add(controller);
    const timer = setTimeout(() => controller.abort(), this.timeout);
    try {
      const response = await this.fetchImpl(target.href, {
        method,
        redirect: 'error',
        signal: controller.signal,
        headers: {
          Authorization: `Bearer ${this.token}`,
          ...(body ? { 'Content-Type': 'application/json' } : {}),
        },
        ...(body ? { body: JSON.stringify(body) } : {}),
      });
      if (response.status === 401 || response.status === 403)
        throw new Error(
          'Home Assistant hat den Zugriff abgelehnt. Bitte Token und Berechtigungen prüfen.',
        );
      if (!response.ok)
        throw new Error(`Home Assistant meldet einen Fehler (HTTP ${response.status}).`);
      return await response.json();
    } catch (error) {
      // Never forward fetch diagnostics, request objects or authentication headers.
      if (/^Home Assistant (hat|meldet)/.test(error.message)) throw error;
      if (controller.signal.aborted)
        throw new Error(
          'Home Assistant antwortet nicht rechtzeitig oder die Anfrage wurde abgebrochen.',
        );
      throw new Error(
        'Home Assistant ist nicht erreichbar. Prüfe Adresse, Netzwerk und eine direkte Verbindung ohne Weiterleitung.',
      );
    } finally {
      clearTimeout(timer);
      this.aborters.delete(controller);
    }
  }
  async testConnection() {
    await this.request('/api/');
    const states = await this.request('/api/states');
    if (!Array.isArray(states))
      throw new Error('Home Assistant hat keine gültige Geräteliste zurückgegeben.');
    const lights = states
      .filter((state) => /^light\.[a-z0-9_]+$/.test(state?.entity_id))
      .map((state) => ({
        id: state.entity_id,
        label: String(state.attributes?.friendly_name || state.entity_id),
      }))
      .sort((a, b) => a.label.localeCompare(b.label, 'de'));
    const message = `Verbindung hergestellt. ${lights.length} Licht-Entitäten gefunden; kein Licht verändert.`;
    this.notify('success', message);
    return { lights, message };
  }
  preview(event) {
    if (!EVENTS.includes(event)) throw new Error('Unbekannte Lichtregel.');
    const rule = this.config.rules[event];
    const action = rule.brightness === 0 ? 'ausschalten' : `auf ${rule.brightness} % dimmen`;
    return {
      description:
        !this.config.enabled || !rule.enabled
          ? `${LABELS[event]}: Regel deaktiviert; es wird kein Lichtbefehl gesendet.`
          : `${LABELS[event]}: ${this.config.entityId} ${action}, Übergang ${rule.transition} Sekunden. Dies ist nur eine Vorschau.`,
    };
  }
  apply(event, { automatic = false, ticket } = {}) {
    if (!EVENTS.includes(event)) return Promise.reject(new Error('Unbekannte Lichtregel.'));
    const revision = this.revision;
    const result = this.queue
      .catch(() => {})
      .then(async () => {
        if (revision !== this.revision || (automatic && ticket !== this.autoTicket))
          return { description: 'Überholte Lichtregel übersprungen.' };
        const rule = this.config.rules[event];
        if (!this.config.enabled || !rule.enabled) {
          const description = this.preview(event).description;
          if (!automatic) this.notify('info', description);
          return { description };
        }
        try {
          const off = rule.brightness === 0;
          await this.request(`/api/services/light/${off ? 'turn_off' : 'turn_on'}`, {
            method: 'POST',
            body: {
              entity_id: this.config.entityId,
              transition: rule.transition,
              ...(!off ? { brightness_pct: rule.brightness } : {}),
            },
          });
          const description = `${LABELS[event]}: Lichtbefehl an ${this.config.entityId} gesendet (${off ? 'aus' : `${rule.brightness} %`}).`;
          this.notify('success', description);
          return { description };
        } catch (error) {
          this.notify('error', error.message);
          throw error;
        }
      });
    this.queue = result;
    return result;
  }
  observePlayback(state, items, meta = {}) {
    const next = {
      status: state.status,
      index: state.index,
      category: items[state.index]?.category,
    };
    const previous = this.previous;
    this.previous = next;
    let event;
    if (
      next.status === 'playing' &&
      (previous.status !== 'playing' ||
        previous.index !== next.index ||
        previous.category !== next.category)
    )
      event = next.category === 'Film' ? 'feature' : 'preshow';
    else if (
      next.status === 'paused' &&
      previous.status !== 'paused' &&
      ['playing', 'blackout'].includes(previous.status)
    )
      event = 'pause';
    else if (
      next.status === 'finished' &&
      previous.status !== 'finished' &&
      ['playing', 'paused', 'blackout'].includes(previous.status)
    )
      event = 'end';
    else if (
      next.status === 'idle' &&
      ['playing', 'paused', 'blackout'].includes(previous.status) &&
      !['error', 'shutdown'].includes(meta.reason)
    )
      event = 'end';
    // Blackout/error cancels queued automatic actions without changing physical light.
    if (event || (next.status !== previous.status && ['blackout', 'error'].includes(next.status)))
      this.autoTicket += 1;
    if (event) this.apply(event, { automatic: true, ticket: this.autoTicket }).catch(() => {});
  }
  close() {
    this.autoTicket += 1;
    this.revision += 1;
    for (const controller of this.aborters) controller.abort();
  }
}

module.exports = { LightingController, defaults, normalizeConfig, normalizeUrl };
