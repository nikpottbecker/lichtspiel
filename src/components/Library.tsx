import { useMemo, useState } from 'react';
import {
  Clapperboard,
  Film,
  Folder,
  Megaphone,
  Plus,
  Search,
  Sparkles,
  Trash2,
} from 'lucide-react';
import type { Category, Media } from '../types';
import './components.css';

interface Props {
  media: Media[];
  onImport: () => void;
  onAdd: (id: string) => void;
  onRemove: (id: string) => void;
  onCategory: (id: string, category: Category) => void;
  locked: boolean;
}

const categories: Category[] = ['Werbung', 'Trailer', 'Film', 'Intro'];
const categoryIcons = { Werbung: Megaphone, Trailer: Clapperboard, Film, Intro: Sparkles };
const categoryClasses = { Werbung: 'advert', Trailer: 'trailer', Film: 'feature', Intro: 'intro' };
function durationLabel(value: number) {
  if (!Number.isFinite(value) || value <= 0) return 'Dauer unbekannt';
  const seconds = Math.floor(value);
  return [Math.floor(seconds / 3600), Math.floor(seconds / 60) % 60, seconds % 60]
    .map((part) => String(part).padStart(2, '0'))
    .join(':');
}

export default function Library({ media, onImport, onAdd, onRemove, onCategory, locked }: Props) {
  const [query, setQuery] = useState('');
  const [category, setCategory] = useState<Category | 'Alle'>('Alle');
  const filtered = useMemo(
    () =>
      media.filter(
        (item) =>
          item.name.toLocaleLowerCase('de').includes(query.toLocaleLowerCase('de')) &&
          (category === 'Alle' || item.category === category),
      ),
    [media, query, category],
  );

  return (
    <section className="library-page">
      <header className="page-header">
        <div>
          <p className="page-kicker">Alles für deinen Filmabend</p>
          <h1>Mediathek</h1>
        </div>
        <button type="button" className="button primary" onClick={onImport} disabled={locked}>
          <Plus size={19} aria-hidden="true" />
          Medien hinzufügen
        </button>
      </header>
      <div className="library-toolbar">
        <label className="search-field">
          <Search size={18} aria-hidden="true" />
          <input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Medien durchsuchen"
            aria-label="Medien durchsuchen"
          />
        </label>
        <label className="library-filter">
          <span className="sr-only">Nach Kategorie filtern</span>
          <select
            value={category}
            onChange={(event) => setCategory(event.target.value as Category | 'Alle')}
          >
            <option value="Alle">Alle Kategorien</option>
            {categories.map((value) => (
              <option key={value}>{value}</option>
            ))}
          </select>
        </label>
        <span className="library-count">
          {filtered.length} {filtered.length === 1 ? 'Datei' : 'Dateien'}
        </span>
      </div>
      {media.length === 0 ? (
        <div className="panel library-empty">
          <Folder size={42} strokeWidth={1.15} aria-hidden="true" />
          <h2>Dein Programm beginnt hier.</h2>
          <p>
            Füge Werbespots, Trailer und Filme hinzu. Anschließend stellst du daraus deinen Ablauf
            zusammen.
          </p>
          <button type="button" className="button primary" onClick={onImport} disabled={locked}>
            <Plus size={18} aria-hidden="true" />
            Erste Medien hinzufügen
          </button>
        </div>
      ) : filtered.length === 0 ? (
        <div className="panel library-empty">
          <Search size={34} strokeWidth={1.4} aria-hidden="true" />
          <h2>Keine passenden Medien</h2>
          <p>Versuche einen anderen Suchbegriff oder eine andere Kategorie.</p>
          <button
            type="button"
            className="button"
            onClick={() => {
              setQuery('');
              setCategory('Alle');
            }}
          >
            Filter zurücksetzen
          </button>
        </div>
      ) : (
        <div className="panel library-list" role="list" aria-label="Importierte Medien">
          {filtered.map((item) => {
            const Icon = categoryIcons[item.category];
            return (
              <article className="library-row" key={item.id} role="listitem">
                <div className={`media-symbol ${categoryClasses[item.category]}`}>
                  <Icon size={24} strokeWidth={1.45} aria-hidden="true" />
                </div>
                <div className="library-name">
                  <strong title={item.name}>{item.name}</strong>
                  <span>
                    {item.demo
                      ? 'Beispiel · keine Videodatei'
                      : item.size > 0
                        ? `${(item.size / (1024 * 1024)).toLocaleString('de', { maximumFractionDigits: 1 })} MB`
                        : 'Lokale Videodatei'}
                  </span>
                </div>
                <span className="library-duration">{durationLabel(item.duration)}</span>
                <select
                  aria-label={`Kategorie für ${item.name}`}
                  value={item.category}
                  onChange={(event) => onCategory(item.id, event.target.value as Category)}
                  disabled={locked}
                >
                  {categories.map((value) => (
                    <option key={value}>{value}</option>
                  ))}
                </select>
                <button
                  type="button"
                  className="button library-add"
                  onClick={() => onAdd(item.id)}
                  disabled={locked}
                  aria-label={`${item.name} zum Ablauf hinzufügen`}
                >
                  <Plus size={17} aria-hidden="true" />
                  <span>Zum Ablauf</span>
                </button>
                <button
                  type="button"
                  className="icon-button"
                  title="Aus Mediathek entfernen"
                  aria-label={`${item.name} aus Mediathek entfernen`}
                  onClick={() => onRemove(item.id)}
                  disabled={locked}
                >
                  <Trash2 size={18} aria-hidden="true" />
                </button>
              </article>
            );
          })}
        </div>
      )}
      {media.length > 0 && (
        <p className="library-footnote">
          {window.cinema
            ? 'Die Originaldateien bleiben an ihrem Speicherort. Verschiebe sie erst, wenn die Vorstellung beendet ist.'
            : 'Deine Videos werden für diese Vorschau lokal im Browser gespeichert. Beim Löschen der Website-Daten gehen diese Kopien verloren.'}
        </p>
      )}
    </section>
  );
}
