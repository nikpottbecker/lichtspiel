import {
  Aperture,
  ArrowDown,
  ArrowUp,
  Clapperboard,
  Film,
  GripVertical,
  Megaphone,
  Monitor,
  Pause,
  Play,
  Plus,
  SkipForward,
  Square,
  Trash2,
  Sparkles,
} from 'lucide-react';
import type { Category, Environment, Media, Playback, Project } from '../types';
import { durationLabel } from '../lib/show.mjs';

const icons = { Werbung: Megaphone, Trailer: Clapperboard, Film, Intro: Sparkles };
export function MediaIcon({ category }: { category: Category }) {
  const Icon = icons[category] || Film;
  return (
    <span className={`media-icon category-${category}`}>
      <Icon size={23} strokeWidth={1.5} />
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
  const total = p.items.reduce((sum, item) => sum + item.duration, 0);
  const elapsed =
    p.playback.status === 'finished'
      ? total
      : p.items.slice(0, p.playback.index).reduce((sum, item) => sum + item.duration, 0) +
        p.playback.position;
  const active = ['playing', 'paused', 'blackout'].includes(p.playback.status);
  const selected = p.environment.displays.find((d) => String(d.id) === p.project.displayId);
  const playingItem = p.items[p.playback.index];
  const statuses = {
    idle: 'Bereit für die große Leinwand',
    playing: 'Vorstellung läuft',
    paused: 'Vorstellung pausiert',
    blackout: 'Schwarzbild · Ton pausiert',
    error: 'Ausgabe unterbrochen',
    finished: 'Vorstellung beendet',
  };
  return (
    <>
      <header className="page-header">
        <div>
          <p className="page-context">Deine nächste Vorstellung</p>
          <input
            aria-label="Name der Vorstellung"
            className="title-input"
            value={p.project.title}
            maxLength={64}
            disabled={p.locked}
            onChange={(e) => p.onChange({ title: e.target.value })}
          />
        </div>
        <button className="button primary" onClick={p.onImport} disabled={p.locked || p.busy}>
          <Plus size={19} />
          Medien hinzufügen
        </button>
      </header>
      <div className="show-columns">
        <section className="panel rundown">
          <div className="section-heading">
            <h2>Ablauf</h2>
            <span>
              {p.items.length} Elemente · {durationLabel(total)}
            </span>
          </div>
          {p.items.length ? (
            <ol className="cue-list">
              {p.items.map((item, index) => (
                <li
                  key={`${item.id}-${index}`}
                  className={`cue-row ${active && p.playback.index === index ? 'current' : ''}`}
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
                  <span className="cue-number">{String(index + 1).padStart(2, '0')}</span>
                  <MediaIcon category={item.category} />
                  <div className="cue-copy">
                    <strong title={item.name}>{item.name}</strong>
                    <span>
                      {item.category}
                      {item.demo ? ' · Beispiel' : ''}
                    </span>
                  </div>
                  <time>{durationLabel(item.duration)}</time>
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
            <h2>Ausgabe</h2>
            {active && (
              <span className="live-dot">
                {p.playback.status === 'playing' ? 'Läuft' : 'Pausiert'}
              </span>
            )}
          </div>
          <div className={`output-canvas ${p.playback.status === 'blackout' ? 'blacked-out' : ''}`}>
            <Aperture size={42} strokeWidth={1} />
            <p>{statuses[p.playback.status]}</p>
            {active && <small>{playingItem?.name}</small>}
          </div>
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
        </section>
      </div>
      <section className="panel timeline-panel">
        <div className="section-heading">
          <h2>Zeitachse</h2>
          <span>Gesamtdauer: {durationLabel(total)}</span>
        </div>
        <div className="timeline" aria-label="Zeitachse des Ablaufs">
          {p.items.length ? (
            p.items.map((item, index) => (
              <div
                className={`timeline-segment category-${item.category}`}
                key={`${item.id}-${index}`}
                style={{ flexGrow: item.duration || 1 }}
                title={`${item.name} · ${durationLabel(item.duration)}`}
              >
                <div className="timeline-bar" />
                <strong>{item.category}</strong>
                <span>{durationLabel(item.duration)}</span>
              </div>
            ))
          ) : (
            <span className="muted">
              Deine Medien erscheinen hier in der geplanten Reihenfolge.
            </span>
          )}
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
              disabled={!p.environment.desktop || active || p.busy}
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
              disabled={p.busy || p.armed || !p.items.length}
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
    </>
  );
}
