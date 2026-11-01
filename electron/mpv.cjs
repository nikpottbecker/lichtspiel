const { EventEmitter } = require('node:events');
const { spawn, execFile } = require('node:child_process');
const net = require('node:net');
const os = require('node:os');
const path = require('node:path');
const fs = require('node:fs/promises');
const { randomUUID } = require('node:crypto');

/** mpv sends newline-delimited JSON, which may arrive across arbitrary chunks. */
class JsonLines {
  constructor(onMessage) {
    this.buffer = '';
    this.onMessage = onMessage;
  }
  push(chunk) {
    this.buffer += chunk.toString();
    if (this.buffer.length > 2 * 1024 * 1024) throw new Error('Ungültige Player-Antwort.');
    let end;
    while ((end = this.buffer.indexOf('\n')) !== -1) {
      const line = this.buffer.slice(0, end).trim();
      this.buffer = this.buffer.slice(end + 1);
      if (!line) continue;
      try {
        this.onMessage(JSON.parse(line));
      } catch {
        /* Ignore non-JSON diagnostics. */
      }
    }
  }
}

function run(binary, args, timeout = 12000) {
  return new Promise((resolve, reject) => {
    execFile(
      binary,
      args,
      { timeout, windowsHide: true, maxBuffer: 1024 * 1024 },
      (error, stdout, stderr) => {
        if (error) reject(new Error('mpv konnte die Datei oder das Gerät nicht öffnen.'));
        else resolve(`${stdout}\n${stderr}`);
      },
    );
  });
}

async function validMpv(binary) {
  if (!binary || typeof binary !== 'string') return false;
  try {
    return /\bmpv\s+v?\d/i.test(await run(binary, ['--version'], 4000));
  } catch {
    return false;
  }
}

async function findMpv(preferred) {
  const executable = process.platform === 'win32' ? 'mpv.exe' : 'mpv';
  const candidates = [
    preferred,
    ...(process.env.PATH || '')
      .split(path.delimiter)
      .filter(Boolean)
      .map((dir) => path.join(dir, executable)),
  ];
  if (process.platform === 'darwin')
    candidates.push(
      '/opt/homebrew/bin/mpv',
      '/usr/local/bin/mpv',
      '/Applications/mpv.app/Contents/MacOS/mpv',
    );
  if (process.platform === 'win32')
    candidates.push(
      path.join(process.env.LOCALAPPDATA || '', 'Programs', 'mpv', 'mpv.exe'),
      'C:\\mpv\\mpv.exe',
    );
  for (const candidate of [...new Set(candidates.filter(Boolean))]) {
    try {
      await fs.access(candidate);
    } catch {
      continue;
    }
    if (await validMpv(candidate)) return candidate;
  }
  return '';
}

async function probeDuration(binary, filename) {
  // The marker is logged at INFO level (mpv's term-msg logger). Filtering all
  // logs to error would suppress it and make every import fail.
  const text = await run(binary, [
    '--no-config',
    '--vo=null',
    '--ao=null',
    '--frames=1',
    '--term-status-msg=',
    '--term-playing-msg=LICHTSPIEL_DURATION=${=duration}',
    '--',
    filename,
  ]);
  const duration = Number(text.match(/LICHTSPIEL_DURATION=([\d.]+)/)?.[1]);
  if (!Number.isFinite(duration) || duration <= 0)
    throw new Error(`Die Laufzeit von „${path.basename(filename)}“ konnte nicht gelesen werden.`);
  return duration;
}

async function audioDevices(binary) {
  if (!binary) return [{ id: 'auto', label: 'Systemstandard' }];
  const text = await run(binary, ['--no-config', '--audio-device=help'], 8000);
  const devices = [...text.matchAll(/^\s*'([^']+)'\s+\((.+)\)\s*$/gm)].map((match) => ({
    id: match[1],
    label: match[1] === 'auto' ? 'Systemstandard' : match[2],
  }));
  return devices.length ? devices : [{ id: 'auto', label: 'Systemstandard' }];
}

async function preflight(items) {
  if (!Array.isArray(items) || !items.length || items.length > 1000)
    throw new Error('Füge zuerst Medien zum Ablauf hinzu (maximal 1000).');
  for (const item of items) {
    if (!item || typeof item.path !== 'string' || !path.isAbsolute(item.path))
      throw new Error('Der Ablauf enthält eine ungültige Datei. Bitte erneut importieren.');
    try {
      const info = await fs.stat(item.path);
      if (!info.isFile() || !info.size) throw new Error();
      await fs.access(item.path, require('node:fs').constants.R_OK);
    } catch {
      throw new Error(`Datei fehlt oder ist nicht lesbar: ${path.basename(item.path)}`);
    }
  }
}

class MpvPlayer extends EventEmitter {
  constructor() {
    super();
    this.state = { status: 'idle', index: 0, position: 0, duration: 0 };
    this.requests = new Map();
    this.serial = 0;
    this.items = [];
    this.intentionalStop = false;
    this.advancing = false;
  }
  update(patch, meta) {
    this.state = { ...this.state, ...patch };
    this.emit('state', this.state, meta);
  }
  active() {
    return !!this.starting || ['playing', 'paused', 'blackout'].includes(this.state.status);
  }
  async start({ binary, items, screenIndex, audioDevice = 'auto' }) {
    if (this.active()) throw new Error('Eine Vorstellung läuft bereits. Bitte zuerst stoppen.');
    if (this.child) await this.stop();
    this.starting = true;
    try {
      await preflight(items);
      if (!(await validMpv(binary)))
        throw new Error('mpv fehlt. Wähle den Player in der Einrichtung aus.');
      this.items = items.map((item) => ({ ...item }));
      this.intentionalStop = false;
      this.endpoint =
        process.platform === 'win32'
          ? `\\\\.\\pipe\\lichtspiel-${process.pid}-${randomUUID()}`
          : path.join(os.tmpdir(), `lichtspiel-${randomUUID()}.sock`);
      const args = [
        '--no-config',
        '--idle=yes',
        '--force-window=yes',
        '--keep-open=no',
        '--fullscreen=yes',
        `--screen=${screenIndex}`,
        `--fs-screen=${screenIndex}`,
        '--no-osc',
        '--osd-level=0',
        '--input-default-bindings=no',
        '--input-vo-keyboard=no',
        '--cursor-autohide=always',
        '--no-input-terminal',
        '--title=Lichtspiel – Leinwand',
        `--audio-device=${audioDevice}`,
        `--input-ipc-server=${this.endpoint}`,
      ];
      const child = spawn(binary, args, {
        windowsHide: false,
        stdio: ['ignore', 'ignore', 'pipe'],
      });
      this.child = child;
      let startupError;
      child.on('error', (error) => {
        startupError = error;
      });
      child.stderr.on('data', () => {});
      child.on('exit', () => {
        if (this.child !== child) return;
        this.child = null;
        this.disconnect();
        if (!this.intentionalStop)
          this.update({
            status: 'error',
            message: 'Die Verbindung zum Player wurde beendet. Prüfe mpv und die Ausgabe.',
          });
      });
      const deadline = Date.now() + 7000;
      while (Date.now() < deadline) {
        if (startupError || child.exitCode !== null)
          throw new Error('mpv konnte nicht gestartet werden. Prüfe Player und Ausgabegerät.');
        try {
          this.socket = await this.connect();
          break;
        } catch {
          await new Promise((resolve) => setTimeout(resolve, 60));
        }
      }
      if (!this.socket) throw new Error('Keine Verbindung zum Player. Bitte mpv neu auswählen.');
      const lines = new JsonLines((message) => this.message(message));
      this.socket.on('data', (chunk) => {
        try {
          lines.push(chunk);
        } catch (error) {
          this.fail(error.message);
        }
      });
      this.socket.on('error', () => {
        if (!this.intentionalStop) this.fail('Die Verbindung zum Player ist abgebrochen.');
      });
      this.socket.on('close', () => {
        if (!this.intentionalStop && this.child) this.fail('Der Player ist nicht mehr erreichbar.');
      });
      await this.command(['observe_property', 1, 'time-pos']);
      await this.command(['observe_property', 2, 'duration']);
      this.update({
        status: 'playing',
        index: 0,
        position: 0,
        duration: items[0].duration || 0,
        message: undefined,
      });
      await this.command(['loadfile', items[0].path, 'replace']);
    } catch (error) {
      this.starting = false;
      await this.stop({ reason: 'error' });
      this.update({ status: 'error', message: error.message });
      throw error;
    } finally {
      this.starting = false;
    }
  }
  connect() {
    return new Promise((resolve, reject) => {
      const socket = net.createConnection(this.endpoint);
      const failed = (error) => {
        socket.destroy();
        reject(error);
      };
      socket.once('error', failed);
      socket.once('connect', () => {
        socket.removeListener('error', failed);
        resolve(socket);
      });
    });
  }
  command(command) {
    if (!this.socket || this.socket.destroyed)
      return Promise.reject(new Error('Player ist nicht verbunden.'));
    return new Promise((resolve, reject) => {
      const id = ++this.serial;
      const timer = setTimeout(() => {
        this.requests.delete(id);
        reject(new Error('Der Player antwortet nicht.'));
      }, 4000);
      this.requests.set(id, { resolve, reject, timer });
      this.socket.write(`${JSON.stringify({ command, request_id: id })}\n`);
    });
  }
  message(message) {
    if (message.request_id) {
      const request = this.requests.get(message.request_id);
      if (request) {
        clearTimeout(request.timer);
        this.requests.delete(message.request_id);
        if (message.error && message.error !== 'success')
          request.reject(new Error(`Player: ${message.error}`));
        else request.resolve(message.data);
      }
    }
    if (message.event === 'property-change' && typeof message.data === 'number') {
      if (message.name === 'time-pos') this.update({ position: message.data });
      if (message.name === 'duration') this.update({ duration: message.data });
    }
    if (message.event === 'end-file' && message.reason === 'eof')
      this.next().catch((error) => this.fail(error.message));
    if (message.event === 'end-file' && message.reason === 'error')
      this.fail('Das Medium konnte nicht abgespielt werden. Bitte Datei und Codec prüfen.');
  }
  async pause() {
    if (this.state.status !== 'playing') return;
    await this.command(['set_property', 'pause', true]);
    this.update({ status: 'paused' });
  }
  async resume() {
    if (!['paused', 'blackout'].includes(this.state.status)) return;
    if (this.state.status === 'blackout') {
      await this.command(['set_property', 'brightness', 0]);
      await this.command(['set_property', 'sub-visibility', true]);
    }
    await this.command(['set_property', 'pause', false]);
    this.update({ status: 'playing' });
  }
  async blackout() {
    if (!['playing', 'paused'].includes(this.state.status)) return;
    await this.command(['set_property', 'pause', true]);
    await this.command(['set_property', 'sub-visibility', false]);
    await this.command(['set_property', 'brightness', -100]);
    this.update({ status: 'blackout' });
  }
  async next() {
    if (this.advancing || !this.child) return;
    this.advancing = true;
    try {
      const index = this.state.index + 1;
      if (index >= this.items.length) {
        await this.command(['stop']);
        this.update({ status: 'finished', position: this.state.duration });
        return;
      }
      // A manual cue change preserves pause/blackout; natural EOF continues playing.
      const status = this.state.status;
      this.update({ index, position: 0, duration: this.items[index].duration || 0 });
      await this.command(['loadfile', this.items[index].path, 'replace']);
      if (status === 'paused' || status === 'blackout')
        await this.command(['set_property', 'pause', true]);
    } finally {
      this.advancing = false;
    }
  }
  fail(message) {
    this.stop({ reason: 'error' }).then(() => this.update({ status: 'error', message }));
  }
  disconnect() {
    for (const request of this.requests.values()) {
      clearTimeout(request.timer);
      request.reject(new Error('Player wurde beendet.'));
    }
    this.requests.clear();
    this.socket?.destroy();
    this.socket = null;
  }
  async stop({ reason = 'user' } = {}) {
    this.intentionalStop = true;
    const child = this.child;
    this.child = null;
    if (this.socket && !this.socket.destroyed)
      this.socket.write(`${JSON.stringify({ command: ['quit'] })}\n`);
    this.disconnect();
    if (child) {
      const kill = setTimeout(() => {
        if (child.exitCode === null) child.kill();
      }, 800);
      kill.unref();
    }
    if (this.endpoint && process.platform !== 'win32')
      await fs.unlink(this.endpoint).catch(() => {});
    this.update(
      { status: 'idle', position: 0, index: 0, duration: 0, message: undefined },
      { reason },
    );
  }
}

module.exports = {
  JsonLines,
  run,
  validMpv,
  findMpv,
  probeDuration,
  audioDevices,
  preflight,
  MpvPlayer,
};
