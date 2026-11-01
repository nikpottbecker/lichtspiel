import type { ReactNode } from 'react';
import { Aperture, Database, Folder, Lightbulb, Play, Settings } from 'lucide-react';
import './components.css';

export type Page = 'show' | 'library' | 'setup' | 'lighting';

interface Props {
  page: Page;
  onNavigate: (page: Page) => void;
  saved: string;
  desktop: boolean;
  children: ReactNode;
}

const navigation = [
  { id: 'show', label: 'Vorstellung', Icon: Play },
  { id: 'library', label: 'Mediathek', Icon: Folder },
  { id: 'lighting', label: 'Lichtsteuerung', Icon: Lightbulb },
  { id: 'setup', label: 'Einrichtung', Icon: Settings },
] as const;

export default function Shell({ page, onNavigate, saved, desktop, children }: Props) {
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <a
          className="brand"
          href="#"
          onClick={(event) => {
            event.preventDefault();
            onNavigate('show');
          }}
          aria-label="Lichtspiel – Vorstellung öffnen"
        >
          <Aperture size={38} strokeWidth={1.25} aria-hidden="true" />
          <span>Lichtspiel</span>
        </a>
        <nav className="main-nav" aria-label="Hauptnavigation">
          {navigation.map(({ id, label, Icon }) => (
            <button
              key={id}
              type="button"
              className={`nav-item ${page === id ? 'active' : ''}`}
              aria-current={page === id ? 'page' : undefined}
              onClick={() => onNavigate(id)}
            >
              <Icon
                size={21}
                strokeWidth={1.6}
                fill={id === 'show' && page === id ? 'currentColor' : 'none'}
                aria-hidden="true"
              />
              <span>{label}</span>
            </button>
          ))}
        </nav>
        <div className="sidebar-bottom">
          {!desktop && <span className="preview-mode">Browser-Vorschau</span>}
          <div className="save-state" role="status">
            <Database size={17} strokeWidth={1.6} aria-hidden="true" />
            <span>{saved}</span>
          </div>
        </div>
      </aside>
      <main className="main-area">{children}</main>
    </div>
  );
}
