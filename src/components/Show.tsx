import { useState } from 'react';
import {
  ArrowDown,
  ArrowUp,
  Clapperboard,
  CircleAlert,
  CircleCheck,
  Film,
  GripVertical,
  Megaphone,
  Monitor,
  Pause,
  Play,
  Plus,
  RefreshCw,
  SkipForward,
  Square,
  Trash2,
  Video,
} from 'lucide-react';
import type { Category, Environment, Media, Playback, Project, Readiness } from '../types';
import { durationLabel } from '../lib/show.mjs';

const icons = { Werbung: Megaphone, Trailer: Clapperboard, Film, Intro: Video };
export function MediaIcon({ category }: { category: Category }) {
  const Icon = icons[category] || Film;
  return (
    <span className="media-icon">
      <Icon size={18} strokeWidth={1.8} />
    </span>
  );
}
interface Props {
  project: Project;
  items: Media[];
  environment: Environment;
  playback: Playback;
  locked: boolean;
  busy: boolean;
  armed: boolean;
  readiness: Readiness | null;
  checking: boolean;
  onCheck: () => void;
  onChange: (patch: Partial<Project>) => void;
  onImport: () => void;
  onMove: (from: number, to: number) => void;
  onRemove: (index: number) => void;
  onStart: () => void;
  onPause: () => void;
  onResume: () => void;
  onStop: () => void;
  onNext: () => void;
  onBlackout: () => void;
  onSchedule: (armed: boolean) => void;
  onDemo: () => void;
}
export default function Show(p: Props) {
  const [selectedIndex, setSelectedIndex] = useState(0);
  const total = p.items.reduce((sum, item) => sum + item.duration, 0);
  const elapsed =
    p.playback.status === 'finished'
      ? total
      : p.items.slice(0, p.playback.index).reduce((sum, item) => sum + item.duration, 0) +
        p.playback.position;
  const active = ['playing', 'paused', 'blackout'].includes(p.playback.status);
  const selected = p.environment.displays.find((d) => String(d.id) === p.project.displayId);
  const playingItem = p.items[p.playback.index];
  const nextItem = p.items[p.playback.index + 1];
  const focusedIndex = active ? p.playback.index : Math.min(selectedIndex, p.items.length - 1);
  const focusedItem = p.items[focusedIndex];
  const cueRemaining = Math.max(0, (playingItem?.duration || 0) - p.playback.position);
  return (
    <div className={`show-page ${active ? 'show-live' : ''}`}>
      <header className="page-header">
        <div>
          <p className="page-context">VORSTELLUNG / REGIE</p>
          <input
            aria-label="Name der Vorstellung"
            className="title-input"
            value={p.project.title}
            maxLength={64}
            disabled={p.locked}
            onChange={(e) => p.onChange({ title: e.target.value })}
          />
        </div>
        <button className="button" onClick={p.onImport} disabled={p.locked || p.busy}>
          <Plus size={19} />
          Medien hinzufügen
        </button>
      </header>
      <div className="show-status-strip" aria-label="Status der Vorstellung">
        <div>
          <span>AUSGABE</span>
          <strong>{selected?.label || 'Nicht gewählt'}</strong>
          <small>{p.environment.desktop ? 'Beamer / Bildschirm' : 'Browser-Vorschau'}</small>
        </div>
        <div>
          <span>WIEDERGABE</span>
          <strong>
            {p.playback.status === 'playing'
              ? 'Läuft'
              : p.playback.status === 'paused'
                ? 'Pausiert'
                : p.playback.status === 'blackout'
                  ? 'Schwarzbild'
                  : p.playback.status === 'error'
                    ? 'Unterbrochen'
                    : p.playback.status === 'finished'
                      ? 'Vorstellung beendet'
                      : 'Nicht gestartet'}
          </strong>
          <small>
            {p.environment.desktop
              ? p.environment.mpvAvailable
                ? 'mpv verfügbar'
                : 'mpv einrichten'
              : 'Eigene Videos im Browser'}
          </small>
        </div>
        <div>
          <span>START</span>
          <strong>{p.armed ? 'Eingeplant' : active ? 'Gestartet' : 'Manuell'}</strong>
          <small>
            {p.project.startAt ? p.project.startAt.replace('T', ' · ') : 'Keine Startzeit'}
          </small>
        </div>
      </div>
      {active && (
        <section className="show-live-focus" aria-label="Aktuelle Wiedergabe">
          <div>
            <span className="show-label">
              JETZT ·{' '}
              {p.playback.status === 'playing'
                ? 'LÄUFT'
                : p.playback.status === 'blackout'
                  ? 'SCHWARZBILD'
                  : 'PAUSIERT'}
            </span>
            <h1>{playingItem?.name || 'Vorstellung'}</h1>
            <div className="show-live-clock">
              <strong>{durationLabel(p.playback.position)}</strong>
              <span>/ {durationLabel(playingItem?.duration || 0)}</span>
            </div>
            <progress
              aria-label="Fortschritt des aktuellen Clips"
              value={p.playback.position}
              max={playingItem?.duration || 1}
            />
            <small>Noch {durationLabel(cueRemaining)}</small>
          </div>
          <div className="show-live-next">
            <span className="show-label">ALS NÄCHSTES</span>
            <strong>{nextItem?.name || 'Ende der Vorstellung'}</strong>
            <small>
              {nextItem
                ? `${nextItem.category} · ${durationLabel(nextItem.duration)}`
                : 'Keine weiteren Medien'}
            </small>
          </div>
        </section>
      )}
      <div className="show-columns">
        <section className="panel rundown">
          <div className="section-heading">
            <h2>Ablauf</h2>
            <span>
              {p.items.length} {p.items.length === 1 ? 'Element' : 'Elemente'} ·{' '}
              {durationLabel(total)}
            </span>
          </div>
          <div className="cue-columns" aria-hidden="true">
            <span>NR.</span>
            <span>ELEMENT</span>
            <span>DAUER</span>
            <span>STATUS</span>
            <span>REIHENFOLGE</span>
          </div>
          {p.items.length ? (
            <ol className="cue-list">
              {p.items.map((item, index) => (
                <li
                  key={`${item.id}-${index}`}
                  className={`cue-row ${focusedIndex === index ? 'current' : ''}`}
                  draggable={!p.locked}
                  onDragStart={(e) => e.dataTransfer.setData('text/plain', String(index))}
                  onDragOver={(e) => e.preventDefault()}
                  onDrop={(e) => {
                    e.preventDefault();
                    if (!p.locked) {
                      const from = Number(e.dataTransfer.getData('text/plain'));
                      if (Number.isInteger(from)) p.onMove(from, index);
                    }
                  }}
                >
                  <GripVertical className="drag-handle" size={17} />
                  <button
                    className="cue-select"
                    type="button"
                    aria-label={`Details zu ${item.name}`}
                    aria-current={focusedIndex === index ? 'true' : undefined}
                    onClick={() => setSelectedIndex(index)}
                  >
                    <span className="cue-number">{String(index + 1).padStart(2, '0')}</span>
                    <span className="cue-identity">
                      <MediaIcon category={item.category} />
                      <span className="cue-copy">
                        <strong title={item.name}>{item.name}</strong>
                        <span>
                          {item.category}
                          {item.demo ? ' · Beispiel' : ''}
                        </span>
                      </span>
                    </span>
                    <time>{durationLabel(item.duration)}</time>
                    <span
                      className={`cue-state ${active && p.playback.index === index ? 'running' : ''}`}
                    >
                      {active
                        ? index < p.playback.index
                          ? 'Gespielt'
                          : index === p.playback.index
                            ? p.playback.status === 'playing'
                              ? 'Läuft'
                              : 'Pausiert'
                            : 'Wartet'
                        : item.demo
                          ? 'Beispiel'
                          : 'Geplant'}
                    </span>
                  </button>
                  <div className="row-actions">
                    <button
                      className="icon-button"
                      aria-label={`${item.name} nach oben`}
                      disabled={p.locked || index === 0}
                      onClick={() => p.onMove(index, index - 1)}
                    >
                      <ArrowUp size={17} />
                    </button>
                    <button
                      className="icon-button"
                      aria-label={`${item.name} nach unten`}
                      disabled={p.locked || index === p.items.length - 1}
                      onClick={() => p.onMove(index, index + 1)}
                    >
                      <ArrowDown size={17} />
                    </button>
                    <button
                      className="icon-button"
                      aria-label={`${item.name} aus Ablauf entfernen`}
                      disabled={p.locked}
                      onClick={() => p.onRemove(index)}
                    >
                      <Trash2 size={17} />
                    </button>
                  </div>
                </li>
              ))}
            </ol>
          ) : (
            <div className="empty-queue">
              <Clapperboard size={38} strokeWidth={1} />
              <h3>Der Abend beginnt mit deinem Ablauf.</h3>
              <p>
                Füge Werbung, Trailer und deinen Film hinzu.
                <br />
                Die Reihenfolge bestimmst du.
              </p>
              <button className="text-button" onClick={p.onDemo}>
                Beispielablauf ansehen
              </button>
            </div>
          )}
          <button className="add-cue" onClick={p.onImport} disabled={p.locked || p.busy}>
            <Plus size={19} />
            Medien zum Ablauf hinzufügen
          </button>
        </section>
        <section className="panel output-panel">
          <div className="section-heading">
            <h2>Details</h2>
            {active && (
              <span className="live-dot">
                {p.playback.status === 'playing'
                  ? 'Läuft'
                  : p.playback.status === 'blackout'
                    ? 'Schwarzbild'
                    : 'Pausiert'}
              </span>
            )}
          </div>
          <div className="cue-details">
            <span className="show-label">
              {focusedItem ? `ELEMENT ${String(focusedIndex + 1).padStart(2, '0')}` : 'ELEMENT'}
            </span>
            <strong>{focusedItem?.name || 'Kein Element gewählt'}</strong>
            {focusedItem ? (
              <dl>
                <div>
                  <dt>Typ</dt>
                  <dd>{focusedItem.category}</dd>
                </div>
                <div>
                  <dt>Dauer</dt>
                  <dd>{durationLabel(focusedItem.duration)}</dd>
                </div>
                <div>
                  <dt>Datei</dt>
                  <dd title={focusedItem.path || focusedItem.name}>
                    {focusedItem.demo
                      ? 'Beispiel · nicht abspielbar'
                      : focusedItem.path || 'Im Browser gespeichert'}
                  </dd>
                </div>
              </dl>
            ) : (
              <p>Wähle ein Element im Ablauf.</p>
            )}
          </div>
          <div className="output-heading show-label">AUSGABE</div>
          <label className="field-label" htmlFor="display-select">
            {p.environment.desktop ? 'Beamer' : 'Ausgabefenster'}
          </label>
          <select
            id="display-select"
            disabled={p.locked}
            value={p.project.displayId}
            onChange={(e) => p.onChange({ displayId: e.target.value })}
          >
            <option value="">Ausgabe wählen</option>
            {p.environment.displays.map((display) => (
              <option key={display.id} value={display.id}>
                {display.label}
                {display.primary ? ' (Hauptbildschirm)' : ''}
              </option>
            ))}
          </select>
          <div className="display-info">
            <Monitor size={16} />
            <span>
              {selected
                ? selected.primary
                  ? 'Ausgabe auf dem Hauptbildschirm'
                  : p.environment.desktop
                    ? 'Externe Ausgabe'
                    : 'Vollbild im Ausgabefenster aktivieren'
                : 'Kein Ausgabegerät ausgewählt'}
            </span>
            {!!selected?.width && (
              <span>
                {selected.width} × {selected.height}
              </span>
            )}
          </div>
          <div className="readiness-panel" aria-live="polite">
            <div className="readiness-heading">
              <div>
                <span className="show-label">STARTPRÜFUNG</span>
                <strong>
                  {p.checking || !p.readiness
                    ? 'Wird geprüft …'
                    : p.readiness?.ready
                      ? 'Bereit für den Start'
                      : 'Prüfung erforderlich'}
                </strong>
              </div>
              <button
                type="button"
                className="icon-button"
                aria-label="Startprüfung erneut ausführen"
                title="Erneut prüfen"
                onClick={p.onCheck}
                disabled={p.checking}
              >
                <RefreshCw size={17} className={p.checking ? 'spinning' : ''} />
              </button>
            </div>
            {p.readiness?.checks.map((check) => (
              <div className="readiness-check" key={check.id}>
                {check.ok ? (
                  <CircleCheck size={17} className="readiness-ok" aria-hidden="true" />
                ) : (
                  <CircleAlert size={17} className="readiness-issue" aria-hidden="true" />
                )}
                <span>
                  <strong>{check.label}</strong>
                  <small>{check.message}</small>
                </span>
              </div>
            ))}
          </div>
        </section>
      </div>
      <section className="panel schedule-panel">
        <div className="section-heading">
          <h2>Zeitsteuerung</h2>
          <span>Einmaliger Start · App geöffnet lassen</span>
        </div>
        <div className="schedule-row">
          <label htmlFor="start-at">Startzeit</label>
          <input
            id="start-at"
            type="datetime-local"
            value={p.project.startAt}
            disabled={p.locked || !p.environment.desktop}
            onChange={(e) => p.onChange({ startAt: e.target.value })}
          />
          <label className="schedule-toggle">
            <input
              type="checkbox"
              role="switch"
              checked={p.armed}
              disabled={
                !p.environment.desktop || active || p.busy || (!p.readiness?.ready && !p.armed)
              }
              onChange={(e) => p.onSchedule(e.target.checked)}
            />
            <span className="switch-track" />
            <span>
              <strong>Automatisch starten</strong>
              <small>
                {!p.environment.desktop
                  ? 'In der Desktop-App verfügbar'
                  : p.armed
                    ? 'Eingeplant · App geöffnet lassen'
                    : 'Einmaliger Start · App geöffnet lassen'}
              </small>
            </span>
          </label>
        </div>
      </section>
      <footer className="transport">
        <div className="time-counter">
          <strong>{durationLabel(elapsed).slice(total < 3600 ? 3 : 0)}</strong>
          <span> / {durationLabel(total).slice(total < 3600 ? 3 : 0)}</span>
        </div>
        <progress aria-label="Fortschritt der Vorstellung" value={elapsed} max={total || 1} />
        <div className="transport-actions">
          {active ? (
            <>
              <button
                className="button primary"
                disabled={p.busy}
                onClick={p.playback.status === 'playing' ? p.onPause : p.onResume}
              >
                {p.playback.status === 'playing' ? <Pause size={20} /> : <Play size={20} />}{' '}
                {p.playback.status === 'playing' ? 'Pause' : 'Fortsetzen'}
              </button>
              <button
                className="icon-button"
                aria-label="Nächster Clip"
                onClick={p.onNext}
                disabled={p.busy}
              >
                <SkipForward />
              </button>
              <button
                className="icon-button"
                aria-label="Vorstellung stoppen"
                onClick={p.onStop}
                disabled={p.busy}
              >
                <Square size={19} />
              </button>
            </>
          ) : (
            <button
              className="button primary"
              onClick={p.onStart}
              disabled={p.busy || p.armed || !p.readiness?.ready}
              title={p.readiness?.checks.find((check) => !check.ok)?.message}
            >
              <Play size={20} fill="currentColor" />
              Vorstellung starten
            </button>
          )}
          <button
            className="button"
            onClick={p.onBlackout}
            disabled={!active || p.busy || p.playback.status === 'blackout'}
          >
            <Monitor size={19} />
            Schwarzbild
          </button>
        </div>
      </footer>
    </div>
  );
}
