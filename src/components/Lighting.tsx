import { useEffect, useState } from 'react';
import {
  AlertCircle,
  Check,
  Eye,
  Lightbulb,
  Link,
  LoaderCircle,
  Save,
  SlidersHorizontal,
  Zap,
} from 'lucide-react';
import type {
  LightEvent as LightingEvent,
  LightRule as LightingRule,
  LightingConfig,
} from '../types';
import './components.css';

const initial: LightingConfig = {
  enabled: false,
  baseUrl: '',
  entityId: '',
  hasToken: false,
  available: true,
  rules: {
    preshow: { enabled: true, brightness: 20, transition: 3 },
    feature: { enabled: true, brightness: 0, transition: 3 },
    pause: { enabled: true, brightness: 40, transition: 2 },
    end: { enabled: true, brightness: 80, transition: 5 },
  },
};
const cues: { id: LightingEvent; title: string; description: string }[] = [
  {
    id: 'preshow',
    title: 'Vorprogramm',
    description: 'Zum Start von Werbung, Trailern oder Intro',
  },
  { id: 'feature', title: 'Hauptfilm', description: 'Wenn ein Clip der Kategorie Film beginnt' },
  { id: 'pause', title: 'Pause', description: 'Wenn du die Vorstellung pausierst' },
  { id: 'end', title: 'Ende', description: 'Nach dem letzten Clip oder beim Stoppen' },
];

export default function Lighting({ desktop }: { desktop: boolean }) {
  const bridge = window.cinema;
  const [config, setConfig] = useState<LightingConfig>(initial);
  const [token, setToken] = useState('');
  const [lights, setLights] = useState<{ id: string; label: string }[]>([]);
  const [loading, setLoading] = useState(desktop);
  const [busy, setBusy] = useState(false);
  const [dirty, setDirty] = useState(false);
  const [notice, setNotice] = useState<{ text: string; error: boolean } | null>(null);
  const [preview, setPreview] = useState<{ event: LightingEvent; description: string } | null>(
    null,
  );
  const nativeReady = desktop && !!bridge?.getLighting;

  useEffect(() => {
    let current = true;
    if (!desktop) return;
    if (!bridge?.getLighting) {
      setLoading(false);
      setConfig((value) => ({ ...value, available: false }));
      setNotice({
        text: 'Die Lichtsteuerung ist in dieser App-Version noch nicht verfügbar.',
        error: true,
      });
      return;
    }
    bridge
      .getLighting()
      .then((value) => {
        if (current) setConfig(value);
      })
      .catch((error) => {
        if (current) {
          setConfig((value) => ({ ...value, available: false }));
          setNotice({
            text:
              error instanceof Error
                ? error.message
                : 'Die Lichtsteuerung konnte nicht geladen werden.',
            error: true,
          });
        }
      })
      .finally(() => {
        if (current) setLoading(false);
      });
    return () => {
      current = false;
    };
  }, [desktop]);

  function patch(values: Partial<LightingConfig>) {
    setConfig((value) => ({ ...value, ...values }));
    setDirty(true);
    setPreview(null);
  }
  function rulePatch(event: LightingEvent, values: Partial<LightingRule>) {
    setConfig((value) => ({
      ...value,
      rules: { ...value.rules, [event]: { ...value.rules[event], ...values } },
    }));
    setDirty(true);
    setPreview(null);
  }
  async function action(run: () => Promise<void>) {
    setBusy(true);
    setNotice(null);
    try {
      await run();
    } catch (error) {
      setNotice({
        text: error instanceof Error ? error.message : 'Die Aktion konnte nicht ausgeführt werden.',
        error: true,
      });
    } finally {
      setBusy(false);
    }
  }
  async function save() {
    if (!bridge?.saveLighting) return;
    await action(async () => {
      const next = await bridge.saveLighting({
        ...config,
        ...(token.trim() ? { token: token.trim() } : {}),
      });
      setConfig(next);
      setToken('');
      setDirty(false);
      setNotice({
        text: 'Lichtsteuerung gespeichert. Es wurde kein Licht verändert.',
        error: false,
      });
    });
  }
  async function checkConnection() {
    if (!bridge?.testLightingConnection) return;
    await action(async () => {
      const result = await bridge.testLightingConnection();
      setLights(result.lights);
      setNotice({
        text: `${result.message} ${result.lights.length} ${result.lights.length === 1 ? 'Licht gefunden' : 'Lichter gefunden'}. Es wurde kein Licht verändert.`,
        error: false,
      });
    });
  }
  async function showPreview(event: LightingEvent) {
    await action(async () => {
      if (nativeReady) {
        const result = await bridge!.previewLighting(event);
        setPreview({ event, description: result.description });
      } else {
        const rule = config.rules[event];
        const description = !config.enabled
          ? 'Die Lichtsteuerung ist ausgeschaltet. Es würde kein Befehl gesendet.'
          : !rule.enabled
            ? 'Diese Regel ist ausgeschaltet. Das Licht würde unverändert bleiben.'
            : `${cues.find((cue) => cue.id === event)!.title}: Licht auf ${rule.brightness} % in ${rule.transition} ${rule.transition === 1 ? 'Sekunde' : 'Sekunden'} einstellen. Dies ist nur eine Vorschau.`;
        setPreview({ event, description });
      }
    });
  }
  async function apply(event: LightingEvent) {
    if (!bridge?.applyLighting) return;
    await action(async () => {
      await bridge.applyLighting(event);
      setNotice({
        text: `Lichtbefehl für „${cues.find((cue) => cue.id === event)!.title}“ gesendet.`,
        error: false,
      });
    });
  }
  const canConnect =
    nativeReady && config.available && !dirty && !busy && !!config.baseUrl && config.hasToken;
  const canApply = canConnect && config.enabled && !!config.entityId;

  return (
    <section className="lighting-page">
      <header className="page-header">
        <div>
          <p className="page-kicker">Das passende Licht zu jedem Moment</p>
          <h1>Lichtsteuerung</h1>
        </div>
        {desktop && (
          <button
            type="button"
            className="button primary"
            disabled={busy || loading || !dirty || !nativeReady || !config.available}
            onClick={() => void save()}
          >
            <Save size={18} aria-hidden="true" />
            Speichern
          </button>
        )}
      </header>
      {!desktop && (
        <div className="lighting-browser-note">
          <Lightbulb size={20} aria-hidden="true" />
          <p>
            Probiere die Lichtabläufe hier aus. Zum Verbinden mit Home Assistant nutze die
            Desktop-App. Diese Vorschau steuert keine Geräte und speichert keine Zugangsdaten.
          </p>
        </div>
      )}
      {notice && (
        <div
          className={`notice ${notice.error ? 'error' : ''}`}
          role={notice.error ? 'alert' : 'status'}
        >
          {notice.error ? (
            <AlertCircle size={18} aria-hidden="true" />
          ) : (
            <Check size={18} aria-hidden="true" />
          )}
          <span>{notice.text}</span>
        </div>
      )}
      {loading ? (
        <div className="lighting-loading" role="status">
          <LoaderCircle className="spinning" size={20} aria-hidden="true" />
          Lichtsteuerung wird geladen …
        </div>
      ) : (
        <>
          <section className="panel lighting-connection">
            <div className="lighting-section-heading">
              <div className="lighting-heading-copy">
                <Lightbulb size={23} strokeWidth={1.5} aria-hidden="true" />
                <div>
                  <h2>Home Assistant</h2>
                  <p>Ein Licht oder eine Lichtgruppe für deinen Kinoraum.</p>
                </div>
              </div>
              <label className="lighting-toggle">
                <input
                  type="checkbox"
                  role="switch"
                  checked={config.enabled}
                  disabled={
                    busy || (desktop && (!config.available || !config.entityId || !config.hasToken))
                  }
                  onChange={(event) => patch({ enabled: event.target.checked })}
                />
                <span className="lighting-switch" />
                <span>Automatisch steuern</span>
              </label>
            </div>
            {desktop && !config.available && (
              <p className="setup-error" role="alert">
                Die Lichtsteuerung ist auf diesem Rechner nicht verfügbar. Prüfe die Einrichtung der
                Desktop-App.
              </p>
            )}
            {desktop ? (
              <>
                <div className="lighting-credentials">
                  <label className="setup-field">
                    Home-Assistant-Adresse
                    <input
                      type="url"
                      placeholder="http://homeassistant.local:8123"
                      value={config.baseUrl}
                      disabled={busy}
                      autoComplete="off"
                      onChange={(event) => {
                        patch({ baseUrl: event.target.value });
                        setLights([]);
                      }}
                    />
                  </label>
                  <label className="setup-field">
                    Zugriffstoken
                    <input
                      type="password"
                      placeholder={
                        config.hasToken
                          ? 'Token gespeichert · zum Ändern neu eingeben'
                          : 'Langlebiges Zugriffstoken einfügen'
                      }
                      value={token}
                      disabled={busy}
                      autoComplete="new-password"
                      spellCheck={false}
                      onChange={(event) => {
                        setToken(event.target.value);
                        setDirty(true);
                      }}
                    />
                  </label>
                </div>
                <p className="lighting-secret-help">
                  Erstelle das Zugriffstoken in deinem Home-Assistant-Profil. Gespeicherte Tokens
                  werden hier nicht wieder angezeigt.
                </p>
                <div className="lighting-device-row">
                  <label className="setup-field">
                    Licht oder Lichtgruppe
                    <select
                      value={config.entityId}
                      disabled={busy}
                      onChange={(event) => patch({ entityId: event.target.value })}
                    >
                      <option value="">Nach Verbindungstest auswählen</option>
                      {config.entityId && !lights.some((light) => light.id === config.entityId) && (
                        <option value={config.entityId}>{config.entityId}</option>
                      )}
                      {lights.map((light) => (
                        <option key={light.id} value={light.id}>
                          {light.label}
                        </option>
                      ))}
                    </select>
                  </label>
                  <button
                    type="button"
                    className="button"
                    disabled={!canConnect}
                    onClick={() => void checkConnection()}
                  >
                    <Link size={17} aria-hidden="true" />
                    Verbindung prüfen
                  </button>
                </div>
                <p className="lighting-connection-help">
                  {dirty
                    ? 'Änderungen zuerst speichern. Danach kannst du die Verbindung prüfen.'
                    : 'Der Verbindungstest liest verfügbare Lichter aus. Er verändert kein Gerät.'}
                  {!config.entityId
                    ? ' Wähle danach ein Licht aus, um die Automatik zu aktivieren.'
                    : ''}
                </p>
              </>
            ) : (
              <p className="lighting-preview-help">
                Aktiviere die Vorschau und passe die vier Lichtregeln an deinen Filmabend an.
              </p>
            )}
          </section>
          <section className="panel lighting-rules">
            <div className="lighting-section-heading">
              <div className="lighting-heading-copy">
                <SlidersHorizontal size={21} strokeWidth={1.5} aria-hidden="true" />
                <div>
                  <h2>Deine Lichtregeln</h2>
                  <p>Die Werte werden beim jeweiligen Ereignis angewendet.</p>
                </div>
              </div>
            </div>
            <div className="lighting-rule-list">
              {cues.map((cue) => {
                const rule = config.rules[cue.id];
                return (
                  <article
                    key={cue.id}
                    className={`lighting-rule ${rule.enabled ? '' : 'disabled'}`}
                  >
                    <div className="lighting-rule-title">
                      <label className="lighting-toggle rule-toggle">
                        <input
                          type="checkbox"
                          role="switch"
                          checked={rule.enabled}
                          disabled={busy}
                          aria-label={`Lichtregel ${cue.title} aktivieren`}
                          onChange={(event) => rulePatch(cue.id, { enabled: event.target.checked })}
                        />
                        <span className="lighting-switch" />
                      </label>
                      <div>
                        <h3>{cue.title}</h3>
                        <p>{cue.description}</p>
                      </div>
                    </div>
                    <div className="lighting-rule-controls">
                      <label className="brightness-field">
                        <span>
                          Helligkeit <output>{rule.brightness} %</output>
                        </span>
                        <input
                          type="range"
                          min="0"
                          max="100"
                          step="1"
                          value={rule.brightness}
                          aria-label={`Helligkeit ${cue.title}`}
                          disabled={busy || !rule.enabled}
                          onChange={(event) =>
                            rulePatch(cue.id, { brightness: Number(event.target.value) })
                          }
                        />
                      </label>
                      <label className="transition-field">
                        <span>Übergang</span>
                        <div>
                          <input
                            type="number"
                            min="0"
                            max="30"
                            step="1"
                            value={rule.transition}
                            aria-label={`Übergang ${cue.title} in Sekunden`}
                            disabled={busy || !rule.enabled}
                            onChange={(event) =>
                              rulePatch(cue.id, {
                                transition: Math.min(30, Math.max(0, Number(event.target.value))),
                              })
                            }
                          />
                          <span>Sek.</span>
                        </div>
                      </label>
                    </div>
                    <div className="lighting-rule-actions">
                      <button
                        type="button"
                        className="button"
                        disabled={busy || (desktop && (dirty || !nativeReady))}
                        onClick={() => void showPreview(cue.id)}
                      >
                        <Eye size={16} aria-hidden="true" />
                        Vorschau
                      </button>
                      {desktop && (
                        <button
                          type="button"
                          className="button test-light"
                          disabled={!canApply || !rule.enabled}
                          onClick={() => void apply(cue.id)}
                        >
                          <Zap size={15} aria-hidden="true" />
                          Licht jetzt testen
                        </button>
                      )}
                    </div>
                    {preview?.event === cue.id && (
                      <div className="lighting-rule-preview" role="status">
                        <Eye size={17} aria-hidden="true" />
                        <p>{preview.description}</p>
                      </div>
                    )}
                  </article>
                );
              })}
            </div>
          </section>
          <p className="lighting-footnote">
            {desktop
              ? '„Vorschau“ zeigt nur den geplanten Befehl. „Licht jetzt testen“ verändert das ausgewählte Licht sofort. Ob sanftes Dimmen unterstützt wird, hängt von deinem Gerät ab.'
              : 'Die Beispielwerte ändern sich nur in dieser Ansicht. Es werden keine Befehle an Home Assistant gesendet.'}
          </p>
        </>
      )}
    </section>
  );
}
