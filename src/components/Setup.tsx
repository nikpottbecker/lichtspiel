import { useEffect, useState } from 'react';
import {
  Aperture,
  ArrowLeft,
  ArrowRight,
  Check,
  CircleCheck,
  FolderOpen,
  Monitor,
  RefreshCw,
  Volume2,
} from 'lucide-react';
import type { Environment, Project } from '../types';
import './components.css';

interface Props {
  environment: Environment;
  project: Project;
  onChange: (patch: Partial<Project>) => void;
  onComplete: () => void;
  onChooseMpv: () => Promise<void>;
  onRefresh: () => Promise<void>;
}

const steps = ['Willkommen', 'Bild & Ton', 'Bereit'];

export default function Setup({
  environment,
  project,
  onChange,
  onComplete,
  onChooseMpv,
  onRefresh,
}: Props) {
  const [step, setStep] = useState(project.onboarded ? 1 : 0);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [projectionNotice, setProjectionNotice] = useState('');
  const [audioDevices, setAudioDevices] = useState<{ id: string; label: string }[]>([]);
  const selectedDisplay = environment.displays.find((display) => display.id === project.displayId);
  const ready = !environment.desktop || (environment.mpvAvailable && !!selectedDisplay);
  useEffect(() => {
    let active = true;
    if (environment.desktop && environment.mpvAvailable && window.cinema?.getAudioDevices) {
      window.cinema
        .getAudioDevices()
        .then((devices) => {
          if (active) setAudioDevices(devices);
        })
        .catch(() => {
          if (active) setAudioDevices([]);
        });
    }
    return () => {
      active = false;
    };
  }, [environment.desktop, environment.mpvAvailable, environment.mpvPath]);

  async function run(action: () => Promise<void>) {
    setBusy(true);
    setError('');
    try {
      await action();
    } catch (reason) {
      setError(
        reason instanceof Error
          ? reason.message
          : 'Die Einrichtung konnte nicht aktualisiert werden.',
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="setup-page">
      <header className="page-header">
        <div>
          <p className="page-kicker">Einmal einrichten. Filmabend für Filmabend.</p>
          <h1>Dein Kino, startklar.</h1>
        </div>
      </header>
      <ol className="setup-steps" aria-label="Einrichtungsschritte">
        {steps.map((label, index) => (
          <li
            key={label}
            className={step === index ? 'current' : step > index ? 'complete' : ''}
            aria-current={step === index ? 'step' : undefined}
          >
            <span>{step > index ? <Check size={16} aria-hidden="true" /> : index + 1}</span>
            {label}
          </li>
        ))}
      </ol>
      <div className="panel setup-panel">
        {step === 0 && (
          <div className="setup-welcome">
            <div className="setup-aperture">
              <Aperture size={58} strokeWidth={1} aria-hidden="true" />
            </div>
            <h2>
              Die große Leinwand.
              <br />
              Dein Ablauf dahinter.
            </h2>
            <p>
              Lichtspiel verbindet Werbung, Trailer und Film zu einer Vorstellung. Du steuerst am
              Rechner, dein Publikum sieht die Ausgabe.
            </p>
            <label className="setup-field">
              Name deiner Vorstellung
              <input
                value={project.title}
                maxLength={80}
                onChange={(event) => onChange({ title: event.target.value })}
                placeholder="Filmabend"
              />
            </label>
            {!environment.desktop && (
              <div className="setup-notice">
                <Monitor size={20} aria-hidden="true" />
                <p>
                  Du bist in der Browser-Vorschau. Hier kannst du Abläufe erstellen und eigene
                  Videos ausprobieren. Für die automatische Beamer-Ausgabe nutze die Desktop-App für
                  macOS oder Windows.
                </p>
              </div>
            )}
          </div>
        )}
        {step === 1 && (
          <div className="setup-devices">
            <div className="setup-section-heading">
              <Monitor size={24} strokeWidth={1.5} aria-hidden="true" />
              <div>
                <h2>Bild & Ton verbinden</h2>
                <p>Schließe deinen Beamer an und wähle die Ausgabe.</p>
              </div>
            </div>
            {environment.desktop && (
              <div className={`player-check ${environment.mpvAvailable ? 'available' : ''}`}>
                <CircleCheck size={21} aria-hidden="true" />
                <div>
                  <strong>
                    {environment.mpvAvailable ? 'mpv gefunden' : 'Wiedergabe einrichten'}
                  </strong>
                  {environment.mpvAvailable ? (
                    <span className="mpv-path" title={environment.mpvPath}>
                      {environment.mpvPath}
                    </span>
                  ) : (
                    <p>
                      Installiere mpv und wähle die ausführbare Datei. Auf macOS geht das mit{' '}
                      <code>brew install mpv</code>; Windows-Downloads findest du unter{' '}
                      <a href="https://mpv.io/installation/" target="_blank" rel="noreferrer">
                        mpv.io
                      </a>
                      .
                    </p>
                  )}
                </div>
                <button
                  type="button"
                  className="button"
                  disabled={busy}
                  onClick={() => void run(onChooseMpv)}
                >
                  <FolderOpen size={16} aria-hidden="true" />
                  {environment.mpvAvailable ? 'Ändern' : 'mpv auswählen'}
                </button>
              </div>
            )}
            {!environment.desktop && (
              <p className="setup-notice standalone">
                Die Browser-Vorschau öffnet Videos in einem eigenen Fenster. Eine zuverlässige
                Bildschirm- und Tonauswahl bietet die Desktop-App.
              </p>
            )}
            <div className="setup-form-grid">
              <label className="setup-field">
                {environment.desktop ? 'Beamer / Bildschirm' : 'Vorschau-Ausgabe'}
                <select
                  value={project.displayId}
                  onChange={(event) => onChange({ displayId: event.target.value })}
                >
                  <option value="">Ausgabe wählen</option>
                  {environment.displays.map((display) => (
                    <option key={display.id} value={display.id}>
                      {display.label}
                      {display.primary ? ' · Hauptbildschirm' : ''}
                    </option>
                  ))}
                </select>
              </label>
              <button
                type="button"
                className="button refresh-button"
                disabled={busy}
                onClick={() => void run(onRefresh)}
              >
                <RefreshCw size={16} aria-hidden="true" />
                Neu erkennen
              </button>
            </div>
            {selectedDisplay && (
              <p className="display-details">
                <Monitor size={15} aria-hidden="true" />
                {selectedDisplay.width > 0 && selectedDisplay.height > 0
                  ? `${selectedDisplay.width} × ${selectedDisplay.height}`
                  : 'Vollbild im Ausgabefenster aktivieren'}
                {selectedDisplay.primary && environment.desktop
                  ? ' · Die Ausgabe liegt auf deinem Hauptbildschirm.'
                  : ''}
              </p>
            )}
            {environment.desktop && selectedDisplay && environment.mpvAvailable && (
              <div className="projection-test">
                <div>
                  <strong>Leinwand prüfen</strong>
                  <p>
                    Zeigt 12 Sekunden lang eine Testkarte über den echten Player. Prüfe, ob sie
                    vollständig und scharf auf dem gewählten Beamer erscheint.
                  </p>
                </div>
                <button
                  type="button"
                  className="button"
                  disabled={busy}
                  onClick={() =>
                    void run(async () => {
                      setProjectionNotice('');
                      await window.cinema?.testProjection(project.displayId);
                      setProjectionNotice(
                        'Test beendet. Bestätige am Beamer selbst, ob Bild und Rand richtig waren.',
                      );
                    })
                  }
                >
                  <Monitor size={16} aria-hidden="true" />
                  {busy ? 'Ausgabe läuft …' : 'Testkarte zeigen'}
                </button>
              </div>
            )}
            {projectionNotice && (
              <p className="setup-help" role="status">
                {projectionNotice}
              </p>
            )}
            {environment.desktop && (
              <>
                <label className="setup-field audio-select">
                  <span>
                    <Volume2 size={17} aria-hidden="true" />
                    Tonausgabe
                  </span>
                  <select
                    value={project.audioDevice || 'auto'}
                    onChange={(event) => onChange({ audioDevice: event.target.value })}
                  >
                    <option value="auto">Systemstandard</option>
                    {audioDevices
                      .filter((device) => device.id !== 'auto')
                      .map((device) => (
                        <option key={device.id} value={device.id}>
                          {device.label}
                        </option>
                      ))}
                  </select>
                </label>
                <p className="setup-help">
                  Verwende einen erweiterten Bildschirm statt Bildschirmspiegelung. Prüfe Bild und
                  Ton mit einem kurzen Clip vor deiner ersten Vorstellung.
                </p>
              </>
            )}
            {error && (
              <p className="setup-error" role="alert">
                {error}
              </p>
            )}
          </div>
        )}
        {step === 2 && (
          <div className="setup-ready">
            <div className="setup-aperture ready">
              <Check size={46} strokeWidth={1.5} aria-hidden="true" />
            </div>
            <h2>Platz für deinen ersten Filmabend.</h2>
            <p>
              Füge jetzt deine Videos hinzu, bringe sie in die richtige Reihenfolge und starte die
              Vorstellung.
            </p>
            <dl className="setup-summary">
              <div>
                <dt>Vorstellung</dt>
                <dd>{project.title.trim() || 'Filmabend'}</dd>
              </div>
              <div>
                <dt>Ausgabe</dt>
                <dd>
                  {selectedDisplay?.label ||
                    (environment.desktop ? 'Noch nicht gewählt' : 'Browser-Vorschau')}
                </dd>
              </div>
              <div>
                <dt>Wiedergabe</dt>
                <dd>
                  {environment.desktop
                    ? 'mpv · lokal auf deinem Rechner'
                    : 'Eigene Videos im Browser'}
                </dd>
              </div>
            </dl>
            <p className="setup-help">
              Dein Ablauf wird lokal gespeichert. Für einen geplanten Start muss die App geöffnet
              und der Rechner wach bleiben.
            </p>
          </div>
        )}
        <footer className="setup-footer">
          {step > 0 ? (
            <button
              type="button"
              className="button"
              onClick={() => setStep((value) => value - 1)}
              disabled={busy}
            >
              <ArrowLeft size={17} aria-hidden="true" />
              Zurück
            </button>
          ) : (
            <span className="setup-private">Lokal. Ohne Konto.</span>
          )}
          <button
            type="button"
            className="button primary"
            disabled={busy || (step >= 1 && !ready)}
            onClick={() => {
              if (step === 2) onComplete();
              else setStep((value) => value + 1);
            }}
          >
            {step === 2 ? 'Zur Vorstellung' : 'Weiter'}
            <ArrowRight size={17} aria-hidden="true" />
          </button>
        </footer>
      </div>
    </section>
  );
}
