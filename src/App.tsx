import { useCallback, useEffect, useRef, useState } from 'react';
import { AlertCircle, Check, LoaderCircle, X } from 'lucide-react';
import Shell from './components/Shell';
import Setup from './components/Setup';
import Library from './components/Library';
import Show from './components/Show';
import Lighting from './components/Lighting';
import { api } from './lib/api';
import { moveItem, scheduledTime, validateShow } from './lib/show.mjs';
import type { Environment, Media, Playback, Project, Readiness, ShowOptions } from './types';

const blank: Project = {
  version: 1,
  title: 'Filmabend',
  library: [],
  queue: [],
  displayId: '',
  audioDevice: 'auto',
  onboarded: false,
  startAt: '',
};
const initialEnv: Environment = {
  desktop: !!window.cinema,
  platform: '',
  displays: [],
  mpvAvailable: false,
  mpvPath: '',
};
export default function App() {
  const [project, setProject] = useState<Project>(blank);
  const [environment, setEnvironment] = useState(initialEnv);
  const [page, setPage] = useState<'show' | 'library' | 'setup' | 'lighting'>('show');
  const [ready, setReady] = useState(false);
  const [canSave, setCanSave] = useState(false);
  const [busy, setBusy] = useState(false);
  const [saved, setSaved] = useState('Wird geladen …');
  const [notice, setNotice] = useState<{ text: string; error: boolean } | null>(null);
  const [armed, setArmed] = useState(false);
  const [readiness, setReadiness] = useState<Readiness | null>(null);
  const [checking, setChecking] = useState(false);
  const [playback, setPlayback] = useState<Playback>({
    status: 'idle',
    index: 0,
    position: 0,
    duration: 0,
  });
  const saveChain = useRef(Promise.resolve());
  const readinessSerial = useRef(0);
  const fail = useCallback(
    (error: unknown) =>
      setNotice({ text: error instanceof Error ? error.message : String(error), error: true }),
    [],
  );
  const update = useCallback(
    (patch: Partial<Project>) => setProject((current) => ({ ...current, ...patch })),
    [],
  );
  const checkReadiness = useCallback(async (options: ShowOptions) => {
    const serial = ++readinessSerial.current;
    setChecking(true);
    setReadiness(null);
    try {
      const result = await api.checkShow(options);
      if (serial === readinessSerial.current) setReadiness(result);
    } catch (error) {
      if (serial === readinessSerial.current)
        setReadiness({
          ready: false,
          checks: [
            {
              id: 'media',
              label: 'Startprüfung',
              ok: false,
              message: error instanceof Error ? error.message : String(error),
            },
          ],
        });
    } finally {
      if (serial === readinessSerial.current) setChecking(false);
    }
  }, []);
  useEffect(() => {
    let cancelled = false;
    Promise.all([api.getEnvironment(), api.loadProject()])
      .then(([env, data]) => {
        if (cancelled) return;
        setEnvironment(env);
        setCanSave(true);
        const loaded = data || blank;
        setProject(loaded);
        setPage(loaded.onboarded ? 'show' : 'setup');
        setReady(true);
      })
      .catch((error) => {
        if (!cancelled) {
          fail(error);
          setSaved('Speichern gesperrt · Ladefehler');
          setReady(true);
          setPage('setup');
        }
      });
    return () => {
      cancelled = true;
    };
  }, [fail]);
  useEffect(
    () =>
      api.onLighting((event) => {
        if (event.status === 'error')
          setNotice({
            text: `Lichtsteuerung: ${event.message} Die Wiedergabe läuft unabhängig davon weiter.`,
            error: true,
          });
      }),
    [],
  );
  useEffect(
    () =>
      api.onPlayback((state) => {
        setPlayback(state);
        if (state.status === 'playing' || state.status === 'error' || state.status === 'finished')
          setArmed(false);
        if (state.status === 'error' && state.message) fail(state.message);
        if (state.status === 'paused' && state.message)
          setNotice({ text: state.message, error: false });
      }),
    [fail],
  );
  useEffect(() => {
    if (!ready || !canSave) return;
    setSaved('Speichert …');
    const timer = setTimeout(() => {
      saveChain.current = saveChain.current
        .then(() => api.saveProject(project))
        .then(() => {
          setSaved('Lokal gespeichert');
        })
        .catch((error) => {
          setSaved('Nicht gespeichert');
          fail(error);
        });
    }, 250);
    return () => clearTimeout(timer);
  }, [project, ready, canSave, fail]);
  const perform = async (action: () => Promise<unknown>) => {
    setBusy(true);
    setNotice(null);
    try {
      await action();
    } catch (error) {
      fail(error);
    } finally {
      setBusy(false);
    }
  };
  const refresh = async () => {
    setEnvironment(await api.getEnvironment());
  };
  const items = project.queue
    .map((id) => project.library.find((item) => item.id === id))
    .filter((item): item is Media => !!item);
  const active = ['playing', 'paused', 'blackout'].includes(playback.status);
  const locked = active || armed || busy;
  const showOptions = { items, displayId: project.displayId, audioDevice: project.audioDevice };
  useEffect(() => {
    if (!ready) return;
    const currentItems = project.queue
      .map((id) => project.library.find((item) => item.id === id))
      .filter((item): item is Media => !!item);
    const options = {
      items: currentItems,
      displayId: project.displayId,
      audioDevice: project.audioDevice,
    };
    const timer = setTimeout(() => void checkReadiness(options), 200);
    const onFocus = () => void checkReadiness(options);
    window.addEventListener('focus', onFocus);
    return () => {
      clearTimeout(timer);
      window.removeEventListener('focus', onFocus);
    };
  }, [
    ready,
    project.queue,
    project.library,
    project.displayId,
    project.audioDevice,
    environment.mpvPath,
    environment.displays,
    checkReadiness,
  ]);
  const importMedia = () => {
    void perform(async () => {
      const media = await api.importMedia();
      if (!media.length) return;
      setProject((current) => ({
        ...current,
        library: [...current.library, ...media],
        queue: [...current.queue, ...media.map((item) => item.id)],
      }));
      setNotice({
        text: `${media.length} ${media.length === 1 ? 'Datei' : 'Dateien'} importiert und zum Ablauf hinzugefügt.`,
        error: false,
      });
    });
  };
  const start = () => {
    void perform(async () => {
      const error = validateShow(items, project.displayId);
      if (error) throw new Error(error);
      await api.startShow(showOptions);
    });
  };
  const schedule = (enabled: boolean) => {
    void perform(async () => {
      if (enabled) {
        const error = validateShow(items, project.displayId);
        if (error) throw new Error(error);
        scheduledTime(project.startAt);
      }
      await api.scheduleShow(
        enabled ? { ...showOptions, at: new Date(project.startAt).toISOString() } : null,
      );
      setArmed(enabled);
      if (enabled)
        setNotice({
          text: 'Vorstellung eingeplant. Lass die App geöffnet und den Rechner wach.',
          error: false,
        });
    });
  };
  const demo = () => {
    const media: Media[] = [
      {
        id: 'demo-welcome',
        name: 'Willkommen',
        duration: 30,
        category: 'Werbung',
        size: 0,
        demo: true,
      },
      {
        id: 'demo-trailer',
        name: 'Kinotrailer',
        duration: 60,
        category: 'Trailer',
        size: 0,
        demo: true,
      },
      { id: 'demo-film', name: 'Hauptfilm', duration: 120, category: 'Film', size: 0, demo: true },
    ];
    setProject((current) => ({
      ...current,
      library: [...current.library.filter((i) => !i.demo), ...media],
      queue: media.map((i) => i.id),
    }));
    setNotice({
      text: 'Beispielablauf zur Orientierung. Zum Abspielen bitte eigene Videos importieren.',
      error: false,
    });
  };
  if (!ready)
    return (
      <div className="loading">
        <LoaderCircle className="spinning" />
        Lichtspiel wird geladen …
      </div>
    );
  return (
    <Shell
      page={page}
      onNavigate={(next) => {
        if (locked && (next === 'setup' || next === 'lighting')) {
          fail(
            'Stoppe die Vorstellung oder deaktiviere die Startzeit, bevor du die Einrichtung änderst.',
          );
          return;
        }
        setPage(next);
      }}
      saved={saved}
      desktop={environment.desktop}
    >
      {!environment.desktop && (
        <div className="preview-notice">
          Browser-Vorschau{' '}
          <span>
            · Oberfläche und eigene Videos ausprobieren. Für Beamerwahl und Zeitsteuerung nutze die
            Desktop-App.
          </span>
        </div>
      )}
      {notice && (
        <div
          role={notice.error ? 'alert' : 'status'}
          className={`notice ${notice.error ? 'error' : ''}`}
        >
          {notice.error ? <AlertCircle size={18} /> : <Check size={18} />}
          <span>{notice.text}</span>
          <button
            aria-label="Hinweis schließen"
            className="icon-button"
            onClick={() => setNotice(null)}
          >
            <X size={16} />
          </button>
        </div>
      )}
      {busy && (
        <div className="busy-message" role="status">
          <LoaderCircle size={15} className="spinning" />
          Wird verarbeitet …
        </div>
      )}
      {page === 'lighting' && <Lighting desktop={environment.desktop} />}
      {page === 'setup' && (
        <Setup
          environment={environment}
          project={project}
          onChange={update}
          onComplete={() => {
            update({ onboarded: true });
            setPage('show');
          }}
          onChooseMpv={async () => {
            try {
              setEnvironment(await api.chooseMpv());
            } catch (error) {
              fail(error);
            }
          }}
          onRefresh={refresh}
        />
      )}
      {page === 'library' && (
        <Library
          media={project.library}
          onImport={importMedia}
          locked={locked || busy}
          onAdd={(id) => {
            update({ queue: [...project.queue, id] });
            setNotice({ text: 'Zum Ablauf hinzugefügt.', error: false });
          }}
          onRemove={(id) => {
            update({
              library: project.library.filter((item) => item.id !== id),
              queue: project.queue.filter((item) => item !== id),
            });
          }}
          onCategory={(id, category) =>
            update({
              library: project.library.map((item) =>
                item.id === id ? { ...item, category } : item,
              ),
            })
          }
        />
      )}
      {page === 'show' && (
        <Show
          project={project}
          items={items}
          environment={environment}
          playback={playback}
          locked={locked}
          busy={busy}
          armed={armed}
          readiness={readiness}
          checking={checking}
          onCheck={() => void checkReadiness(showOptions)}
          onChange={update}
          onImport={importMedia}
          onMove={(from, to) => update({ queue: moveItem(project.queue, from, to) })}
          onRemove={(index) => update({ queue: project.queue.filter((_, i) => i !== index) })}
          onStart={start}
          onPause={() => void perform(() => api.pauseShow())}
          onResume={() => void perform(() => api.resumeShow())}
          onStop={() => void perform(() => api.stopShow())}
          onNext={() => void perform(() => api.nextCue())}
          onBlackout={() => void perform(() => api.blackout())}
          onSchedule={schedule}
          onDemo={demo}
        />
      )}
    </Shell>
  );
}
