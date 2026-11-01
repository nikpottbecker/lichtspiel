import type { CinemaAPI, Media, Playback, Project, ShowOptions } from '../types';

const listeners = new Set<(state: Playback) => void>();
let state: Playback = { status: 'idle', index: 0, position: 0, duration: 0 };
let output: Window | null = null;
let video: HTMLVideoElement | null = null;
let queue: Media[] = [];
let watch: ReturnType<typeof setInterval> | undefined;
function emit(patch: Partial<Playback>) {
  state = { ...state, ...patch };
  listeners.forEach((cb) => cb({ ...state }));
}
async function playWithPermission() {
  if (!video || !output || output.closed) throw new Error('Das Ausgabefenster ist geschlossen.');
  try {
    await video.play();
    output.document.getElementById('play-permission')?.remove();
    emit({ status: 'playing', message: undefined });
  } catch (error) {
    if (
      !error ||
      typeof error !== 'object' ||
      !('name' in error) ||
      error.name !== 'NotAllowedError'
    )
      throw error;
    // A new browsing context may require its own user gesture for audible media.
    // Keep this restriction visible instead of muting the movie or faking progress.
    let button = output.document.getElementById('play-permission') as HTMLButtonElement | null;
    if (!button) {
      button = output.document.createElement('button');
      button.id = 'play-permission';
      button.textContent = 'Wiedergabe freigeben';
      button.style.cssText =
        'position:fixed;left:50%;top:50%;transform:translate(-50%,-50%);background:#ffba5b;color:#21190e;border:0;border-radius:7px;font:16px system-ui;padding:16px 24px;cursor:pointer;';
      button.onclick = () => {
        void playWithPermission().catch(handleError);
      };
      output.document.body.append(button);
    }
    button.style.visibility = 'visible';
    emit({
      status: 'paused',
      message:
        'Klicke im Ausgabefenster auf „Wiedergabe freigeben“, damit der Browser Bild und Ton starten darf.',
    });
  }
}
const db = () =>
  new Promise<IDBDatabase>((resolve, reject) => {
    const req = indexedDB.open('lichtspiel-media', 1);
    req.onupgradeneeded = () => req.result.createObjectStore('files');
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
async function fileStore(id: string, blob?: Blob) {
  const database = await db();
  return new Promise<Blob | undefined>((resolve, reject) => {
    const tx = database.transaction('files', blob ? 'readwrite' : 'readonly');
    const req = blob ? tx.objectStore('files').put(blob, id) : tx.objectStore('files').get(id);
    tx.oncomplete = () => {
      database.close();
      resolve(blob || req.result);
    };
    tx.onerror = () => {
      database.close();
      reject(tx.error);
    };
  });
}
async function metadata(file: File): Promise<Media> {
  const url = URL.createObjectURL(file);
  const duration = await new Promise<number>((resolve, reject) => {
    const probe = document.createElement('video');
    const cleanup = () => {
      clearTimeout(timeout);
      probe.removeAttribute('src');
      probe.load();
    };
    const timeout = setTimeout(() => {
      cleanup();
      reject(new Error(`${file.name}: Laufzeit konnte nicht gelesen werden.`));
    }, 10000);
    probe.preload = 'metadata';
    probe.onloadedmetadata = () => {
      const seconds = probe.duration;
      cleanup();
      Number.isFinite(seconds) && seconds > 0
        ? resolve(seconds)
        : reject(new Error(`${file.name}: Keine gültige Videolaufzeit.`));
    };
    probe.onerror = () => {
      cleanup();
      reject(
        new Error(
          `${file.name}: Dieses Format wird vom Browser nicht unterstützt. Nutze die Desktop-App.`,
        ),
      );
    };
    probe.src = url;
  }).catch((error) => {
    URL.revokeObjectURL(url);
    throw error;
  });
  const id = crypto.randomUUID();
  await fileStore(id, file);
  return {
    id,
    name: file.name.replace(/\.[^.]+$/, ''),
    duration,
    category: 'Film',
    size: file.size,
    url,
  };
}
async function load(index: number) {
  if (!video || !output || output.closed)
    throw new Error('Das Ausgabefenster ist geschlossen. Starte die Vorstellung erneut.');
  if (index >= queue.length) {
    clearInterval(watch);
    video.pause();
    video.removeAttribute('src');
    video.load();
    emit({ status: 'finished', position: 0 });
    return;
  }
  emit({ index, position: 0, duration: queue[index].duration });
  video.style.visibility = 'visible';
  video.src = queue[index].url!;
  await playWithPermission();
}
const handleError = (error: unknown) =>
  emit({ status: 'error', message: error instanceof Error ? error.message : String(error) });

export const browserAPI: CinemaAPI = {
  async getEnvironment() {
    return {
      desktop: false,
      platform: 'browser',
      displays: [
        { id: 'browser', label: 'Separates Browserfenster', width: 0, height: 0, primary: false },
      ],
      mpvAvailable: false,
      mpvPath: '',
    };
  },
  async chooseMpv() {
    throw new Error('mpv wird in der Desktop-App eingerichtet.');
  },
  async getAudioDevices() {
    return [{ id: 'auto', label: 'Standardausgabe des Browsers' }];
  },
  importMedia() {
    return new Promise((resolve, reject) => {
      const input = document.createElement('input');
      input.type = 'file';
      input.accept = 'video/*';
      input.multiple = true;
      input.oncancel = () => resolve([]);
      input.onchange = async () => {
        try {
          const imported: Media[] = [];
          for (const file of Array.from(input.files || [])) imported.push(await metadata(file));
          resolve(imported);
        } catch (error) {
          reject(error);
        }
      };
      input.click();
    });
  },
  async startShow(options: ShowOptions) {
    // Open synchronously inside the click gesture so browsers can allow the output.
    if (!output || output.closed)
      output = window.open('', 'lichtspiel-output', 'popup,width=960,height=540');
    if (!output) throw new Error('Bitte erlaube Pop-ups für das Ausgabefenster und starte erneut.');
    if (!video || video.ownerDocument !== output.document || !video.isConnected) {
      output.document.title = 'Lichtspiel · Ausgabe';
      output.document.body.style.cssText =
        'margin:0;background:#000;height:100vh;overflow:hidden;display:grid;place-items:center;';
      output.document.body.replaceChildren();
      video = output.document.createElement('video');
      video.style.cssText = 'width:100vw;height:100vh;object-fit:contain;background:black;';
      video.controls = false;
      video.playsInline = true;
      output.document.body.append(video);
      const hint = output.document.createElement('button');
      hint.textContent = 'Vollbild';
      hint.style.cssText =
        'position:fixed;right:16px;bottom:16px;padding:8px 12px;color:#fff;background:#222;border:1px solid #555;border-radius:6px;cursor:pointer';
      hint.onclick = () => {
        output?.document.documentElement.requestFullscreen().catch(handleError);
      };
      output.document.onfullscreenchange = () => {
        hint.style.display = output?.document.fullscreenElement ? 'none' : 'block';
      };
      output.document.body.append(hint);
      video.ontimeupdate = () => emit({ position: video?.currentTime || 0 });
      video.onended = () => {
        void load(state.index + 1).catch(handleError);
      };
      video.onerror = () =>
        handleError(
          new Error('Die Videodatei konnte nicht abgespielt werden. Bitte erneut importieren.'),
        );
    }
    queue = options.items;
    clearInterval(watch);
    watch = setInterval(() => {
      if (output?.closed) {
        clearInterval(watch);
        video = null;
        handleError(new Error('Das Ausgabefenster wurde geschlossen.'));
      }
    }, 750);
    await load(0);
  },
  async pauseShow() {
    video?.pause();
    emit({ status: 'paused' });
  },
  async resumeShow() {
    if (!video || output?.closed) throw new Error('Kein Ausgabefenster geöffnet.');
    video.style.visibility = 'visible';
    await playWithPermission();
  },
  async stopShow() {
    video?.pause();
    if (video) {
      video.removeAttribute('src');
      video.load();
    }
    output?.document.getElementById('play-permission')?.remove();
    clearInterval(watch);
    emit({ status: 'idle', index: 0, position: 0, duration: 0 });
  },
  async nextCue() {
    await load(state.index + 1);
  },
  async blackout() {
    video?.pause();
    if (video) video.style.visibility = 'hidden';
    const button = output?.document.getElementById('play-permission');
    if (button) button.style.visibility = 'hidden';
    emit({ status: 'blackout' });
  },
  onPlayback(cb) {
    listeners.add(cb);
    return () => {
      listeners.delete(cb);
    };
  },
  async saveProject(data: Project) {
    localStorage.setItem(
      'lichtspiel-project',
      JSON.stringify({ ...data, library: data.library.map(({ url, ...item }) => item) }),
    );
  },
  async loadProject() {
    const raw = localStorage.getItem('lichtspiel-project');
    if (!raw) return null;
    const project = JSON.parse(raw) as Project;
    if (project.version !== 1 || !Array.isArray(project.library) || !Array.isArray(project.queue))
      throw new Error('Die gespeicherte Vorstellung hat ein unbekanntes Format.');
    for (const item of project.library) {
      if (!item.demo) {
        const file = await fileStore(item.id);
        if (file) item.url = URL.createObjectURL(file);
      }
    }
    return project;
  },
  async scheduleShow(options) {
    if (options) throw new Error('Automatische Startzeiten sind in der Desktop-App verfügbar.');
  },
  async getLighting() {
    return {
      enabled: false,
      baseUrl: '',
      entityId: '',
      hasToken: false,
      available: false,
      rules: {
        preshow: { enabled: true, brightness: 20, transition: 3 },
        feature: { enabled: true, brightness: 0, transition: 3 },
        pause: { enabled: true, brightness: 40, transition: 2 },
        end: { enabled: true, brightness: 80, transition: 5 },
      },
    };
  },
  async saveLighting() {
    throw new Error('Die Smarthome-Verbindung wird in der Desktop-App gespeichert.');
  },
  async testLightingConnection() {
    throw new Error('Verbinde Home Assistant in der Desktop-App.');
  },
  async previewLighting() {
    return { description: 'Vorschau: Es wird kein Befehl an Lampen gesendet.' };
  },
  async applyLighting() {
    throw new Error('Lichtsteuerung ist nur in der Desktop-App verfügbar.');
  },
  onLighting() {
    return () => {};
  },
};

window.addEventListener('beforeunload', () => {
  output?.close();
});
