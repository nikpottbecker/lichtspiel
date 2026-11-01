const {
  app,
  BrowserWindow,
  ipcMain,
  dialog,
  screen,
  protocol,
  net,
  powerSaveBlocker,
  shell,
  safeStorage,
} = require('electron');
const fs = require('node:fs/promises');
const path = require('node:path');
const { pathToFileURL } = require('node:url');
const { randomUUID } = require('node:crypto');
const {
  MpvPlayer,
  findMpv,
  validMpv,
  probeDuration,
  audioDevices,
  preflight,
} = require('./mpv.cjs');
const { ShowScheduler } = require('./scheduler.cjs');
const { LightingController } = require('./lighting.cjs');

protocol.registerSchemesAsPrivileged([
  {
    scheme: 'lichtspiel-media',
    privileges: { standard: true, secure: true, supportFetchAPI: true, stream: true },
  },
]);
let mainWindow;
let mpvPath = '';
let settings = {};
let sleepBlocker;
let lighting;
const mediaTokens = new Map();
let saveQueue = Promise.resolve();
const player = new MpvPlayer();
const settingsFile = () => path.join(app.getPath('userData'), 'settings.json');
const projectFile = () => path.join(app.getPath('userData'), 'project.json');
const isBusy = () => player.active();

function displays() {
  const primary = screen.getPrimaryDisplay().id;
  return screen.getAllDisplays().map((display, index) => ({
    id: String(display.id),
    label: display.label || `Bildschirm ${index + 1}`,
    width: display.size.width,
    height: display.size.height,
    primary: display.id === primary,
  }));
}

function environment() {
  return {
    desktop: true,
    platform: process.platform,
    displays: displays(),
    mpvAvailable: !!mpvPath,
    mpvPath,
  };
}

async function atomicJson(file, data) {
  const serialized = JSON.stringify(data, null, 2);
  if (serialized.length > 5 * 1024 * 1024)
    throw new Error('Das Projekt ist zu groß (maximal 5 MB).');
  await fs.mkdir(path.dirname(file), { recursive: true });
  const temporary = `${file}.${randomUUID()}.tmp`;
  await fs.writeFile(temporary, serialized, { mode: 0o600 });
  await fs.rename(temporary, file);
}

function mediaUrl(filename) {
  const token = randomUUID();
  mediaTokens.set(token, filename);
  return `lichtspiel-media://local/${token}`;
}

function hydrateMedia(value) {
  if (Array.isArray(value)) return value.map(hydrateMedia);
  if (!value || typeof value !== 'object') return value;
  const result = Object.fromEntries(
    Object.entries(value).map(([key, child]) => [key, hydrateMedia(child)]),
  );
  if (
    typeof result.path === 'string' &&
    path.isAbsolute(result.path) &&
    /\.(mp4|m4v|mov|mkv|webm|avi|mpg|mpeg)$/i.test(result.path)
  )
    result.url = mediaUrl(result.path);
  return result;
}

async function startShow(show) {
  if (!show || typeof show.displayId !== 'string')
    throw new Error('Wähle zuerst den Bildschirm für die Ausgabe.');
  // Electron and mpv expose different display APIs. Both normally enumerate physical
  // displays in OS order; verify the selected output with a test clip on real hardware.
  const all = screen.getAllDisplays();
  const screenIndex = all.findIndex((display) => String(display.id) === show.displayId);
  if (screenIndex < 0)
    throw new Error(
      'Der gewählte Bildschirm ist nicht mehr verbunden. Bitte in der Einrichtung neu auswählen.',
    );
  const audioDevice =
    typeof show.audioDevice === 'string' && show.audioDevice.length < 1024
      ? show.audioDevice
      : 'auto';
  await player.start({ binary: mpvPath, items: show.items, screenIndex, audioDevice });
}

const scheduler = new ShowScheduler({
  start: startShow,
  isBusy,
  onError: (message) => {
    // Report a scheduling problem without corrupting the state of a running show.
    if (player.active())
      mainWindow?.webContents.send('cinema:playback', { ...player.state, message });
    else player.update({ status: 'error', message });
  },
});

function syncSleepBlocker() {
  const needed = player.active() || !!scheduler.pending;
  if (needed && (sleepBlocker === undefined || !powerSaveBlocker.isStarted(sleepBlocker)))
    sleepBlocker = powerSaveBlocker.start('prevent-display-sleep');
  if (!needed && sleepBlocker !== undefined) {
    powerSaveBlocker.stop(sleepBlocker);
    sleepBlocker = undefined;
  }
}

player.on('state', (state, meta) => {
  if (mainWindow && !mainWindow.isDestroyed())
    mainWindow.webContents.send('cinema:playback', state);
  lighting?.observePlayback(state, player.items, meta);
  syncSleepBlocker();
});

function handle(name, callback) {
  ipcMain.handle(`cinema:${name}`, async (event, ...args) => {
    if (
      !mainWindow ||
      event.sender !== mainWindow.webContents ||
      event.senderFrame !== mainWindow.webContents.mainFrame
    )
      throw new Error('Nicht erlaubte Anfrage.');
    return callback(...args);
  });
}

function registerHandlers() {
  handle('lighting-get', () => lighting.publicConfig());
  handle('lighting-save', (input) => lighting.save(input));
  handle('lighting-test', () => lighting.testConnection());
  handle('lighting-preview', (event) => lighting.preview(event));
  handle('lighting-apply', (event) => lighting.apply(event));
  handle('environment', async () => {
    mpvPath = await findMpv(settings.mpvPath);
    return environment();
  });
  handle('choose-mpv', async () => {
    const result = await dialog.showOpenDialog(mainWindow, {
      title: 'mpv-Programm auswählen',
      properties: ['openFile'],
      ...(process.platform === 'win32' ? { filters: [{ name: 'mpv', extensions: ['exe'] }] } : {}),
    });
    if (!result.canceled && result.filePaths[0]) {
      const selected = result.filePaths[0];
      if (!(await validMpv(selected)))
        throw new Error('Das ausgewählte Programm ist kein funktionierender mpv-Player.');
      mpvPath = selected;
      settings.mpvPath = selected;
      await atomicJson(settingsFile(), settings);
    }
    return environment();
  });
  handle('import', async () => {
    if (!mpvPath) throw new Error('Bitte zuerst mpv in der Einrichtung auswählen.');
    const result = await dialog.showOpenDialog(mainWindow, {
      title: 'Medien importieren',
      properties: ['openFile', 'multiSelections'],
      filters: [
        {
          name: 'Videodateien',
          extensions: ['mp4', 'm4v', 'mov', 'mkv', 'webm', 'avi', 'mpg', 'mpeg'],
        },
      ],
    });
    if (result.canceled) return [];
    const imported = [];
    for (const filename of result.filePaths) {
      const stat = await fs.stat(filename);
      if (!stat.isFile() || !stat.size)
        throw new Error(`Datei ist leer: ${path.basename(filename)}`);
      const duration = await probeDuration(mpvPath, filename);
      imported.push({
        id: randomUUID(),
        name: path.basename(filename, path.extname(filename)),
        path: filename,
        duration,
        category: 'Film',
        size: stat.size,
        url: mediaUrl(filename),
      });
    }
    return imported;
  });
  handle('audio-devices', () => audioDevices(mpvPath));
  handle('start', startShow);
  handle('pause', () => player.pause());
  handle('resume', () => player.resume());
  handle('stop', () => player.stop());
  handle('next', () => player.next());
  handle('blackout', () => player.blackout());
  handle('save', async (data) => {
    if (!data || typeof data !== 'object' || Array.isArray(data))
      throw new Error('Ungültiges Projekt.');
    // Keep the order of renderer autosaves, including when disks are slow.
    const save = saveQueue.catch(() => {}).then(() => atomicJson(projectFile(), data));
    saveQueue = save;
    await save;
  });
  handle('load', async () => {
    try {
      return hydrateMedia(JSON.parse(await fs.readFile(projectFile(), 'utf8')));
    } catch (error) {
      if (error.code === 'ENOENT') return null;
      throw new Error('Das gespeicherte Projekt konnte nicht gelesen werden.');
    }
  });
  handle('schedule', async (show) => {
    if (show !== null) {
      await preflight(show?.items);
      if (!mpvPath) throw new Error('Bitte zuerst mpv in der Einrichtung auswählen.');
      if (!displays().some((display) => display.id === show.displayId))
        throw new Error('Der gewählte Ausgabebildschirm ist nicht verbunden.');
    }
    scheduler.arm(show);
    syncSleepBlocker();
  });
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1440,
    height: 960,
    minWidth: 860,
    minHeight: 640,
    backgroundColor: '#141516',
    title: 'Lichtspiel',
    autoHideMenuBar: true,
    webPreferences: {
      preload: path.join(__dirname, 'preload.cjs'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
      webSecurity: true,
    },
  });
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    try {
      const target = new URL(url);
      if (target.protocol === 'https:' && target.hostname === 'mpv.io')
        shell.openExternal(target.href).catch(() => {});
    } catch {
      /* Ignore malformed destinations. */
    }
    return { action: 'deny' };
  });
  mainWindow.webContents.on('will-navigate', (event) => event.preventDefault());
  const devUrl = process.env.VITE_DEV_SERVER_URL;
  if (devUrl && /^http:\/\/(localhost|127\.0\.0\.1):\d+\/?$/.test(devUrl))
    mainWindow.loadURL(devUrl);
  else mainWindow.loadFile(path.join(__dirname, '..', 'dist', 'index.html'));
  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

if (!app.requestSingleInstanceLock()) app.quit();
else {
  app.on('second-instance', () => {
    if (mainWindow) {
      if (mainWindow.isMinimized()) mainWindow.restore();
      mainWindow.focus();
    }
  });
  app
    .whenReady()
    .then(async () => {
      lighting = new LightingController({
        filename: path.join(app.getPath('userData'), 'lighting.json'),
        secureStorage: safeStorage,
      });
      lighting.on('notice', (notice) => {
        if (mainWindow && !mainWindow.isDestroyed())
          mainWindow.webContents.send('cinema:lighting', notice);
      });
      await lighting.load();
      try {
        settings = JSON.parse(await fs.readFile(settingsFile(), 'utf8'));
      } catch {
        settings = {};
      }
      mpvPath = await findMpv(settings.mpvPath);
      protocol.handle('lichtspiel-media', (request) => {
        const url = new URL(request.url);
        const filename = url.hostname === 'local' && mediaTokens.get(url.pathname.slice(1));
        if (!filename) return new Response('Not found', { status: 404 });
        return net.fetch(pathToFileURL(filename).href, { headers: request.headers });
      });
      registerHandlers();
      createWindow();
      const timer = setInterval(() => scheduler.tick().finally(syncSleepBlocker), 500);
      timer.unref();
    })
    .catch((error) => {
      dialog.showErrorBox('Lichtspiel konnte nicht starten', error.message);
      app.quit();
    });
  app.on('window-all-closed', () => app.quit());
  app.on('before-quit', () => {
    scheduler.arm(null);
    lighting?.close();
    player.stop({ reason: 'shutdown' });
  });
}
