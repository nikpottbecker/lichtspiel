# Lokal entwickeln

[← Zur Projektübersicht](../README.md)

Lichtspiel besteht aus einer React-/TypeScript-Oberfläche, einer Electron-Hülle und einem separat installierten mpv-Player. Home Assistant ist optional.

## Voraussetzungen

- Node.js 22 oder 24 mit npm und Git.
- mpv für native Medienimporte und Wiedergabe.
- Chromium von Playwright und `ffmpeg` im Suchpfad für Browser-Tests.
- Ein reales macOS- oder Windows-System für die abschließende Geräteprüfung und die jeweilige Paketierung.

```sh
git clone https://github.com/nikpottbecker/lichtspiel.git
cd lichtspiel
npm ci
```

## Entwicklungsmodi

| Befehl                 | Zweck                                                        |
| ---------------------- | ------------------------------------------------------------ |
| `npm run dev`          | Vite und die Electron-Desktop-App starten.                   |
| `npm run dev:web`      | Nur die Browseroberfläche starten.                           |
| `npm run check`        | Formatprüfung, Logiktests und Produktionsbuild ausführen.    |
| `npm run typecheck`    | TypeScript prüfen.                                           |
| `npm run build`        | TypeScript prüfen und einen Produktionsbuild erzeugen.       |
| `npm test`             | Logik-, Scheduler-, IPC- und Lichtsteuerungstests ausführen. |
| `npm run test:browser` | Den Testserver starten und beide Browserprüfungen ausführen. |
| `npm run format`       | Die Projektdateien formatieren.                              |
| `npm run format:check` | Die Formatierung ohne Änderungen prüfen.                     |
| `npm run package:mac`  | Auf macOS ein Desktop-Paket erzeugen.                        |
| `npm run package:win`  | Auf Windows ein Desktop-Paket erzeugen.                      |

Der Entwicklungsserver verwendet Port 5173. Desktop und Browser haben unterschiedliche Adapter; Hardwarezugriff darf nicht in den Browseradapter wandern.

## Projektaufbau

```text
lichtspiel/
├── src/
│   ├── components/     Oberfläche, Einrichtung und Lichtregeln
│   ├── lib/            Browseradapter und gemeinsame Ablauflogik
│   └── types.ts        Vertrag zwischen Oberfläche und Desktop
├── electron/
│   ├── main.cjs        Fenster, Dateizugriff und IPC
│   ├── preload.cjs     Eng begrenzte Desktop-Schnittstelle
│   ├── mpv.cjs         Player-Prozess und JSON-IPC
│   ├── scheduler.cjs   Einmalige Startzeiten
│   └── lighting.cjs    Home-Assistant-Verbindung und Lichtregeln
├── tests/              Ablauf- und Browser-Tests
├── docs/               Anleitungen und Architektur
└── design/             Entwurf und dokumentierte UI-Prüfung
```

## Prüfen

### Logik und Build

```sh
npm run check
```

Die Home-Assistant-Tests verwenden simulierte HTTP-Antworten und simulierte sichere Speicherung. Sie senden keine Befehle an reale Geräte.

### Browserabläufe

Installiere `ffmpeg` über die Paketverwaltung deines Betriebssystems und anschließend Chromium:

```sh
npx playwright install chromium
npm run test:browser
```

Der Testbefehl verwaltet den Vite-Server selbst. Der erste Test erzeugt einen kurzen Clip im temporären Verzeichnis des Betriebssystems und prüft Einrichtung, Import, Sortierung, Speicherung, tatsächliche Browserwiedergabe, Pause, Schwarzbild und Lichtvorschau. Der zweite prüft den Desktop-Vertrag der Lichtoberfläche mit einer simulierten Bridge und schützt gegen Überschreiben eines beschädigten Projekts.

Die einzelnen Skripte `node tests/browser.mjs` und `node tests/lighting-ui.mjs` können auch gegen einen bereits laufenden Server auf `http://localhost:5173` ausgeführt werden. Bei einer fehlenden Chromium-Systembibliothek hilft unter Linux `npx playwright install --with-deps chromium`, sofern die Umgebung Paketinstallationen erlaubt.

### Native Ausgabe

Die JSON-IPC-Steuerung wurde mit echtem mpv 0.40 unter Linux und Nullausgabe geprüft. Damit wurden Laufzeitmessung, Start, Pause, Schwarzbild, Fortsetzen und Clipwechsel geprüft. Es ist keine Bestätigung der Monitorzuordnung, Bildqualität oder Audioausgabe auf macOS und Windows.

Für einen Hardwarebericht sind Betriebssystem, CPU-Architektur, mpv-Version, Bildschirmaufbau, Tonweg, Codecs und reproduzierbare Schritte hilfreich. Verwende für reproduzierbare Tests eigene kurze Clips ohne persönliche Daten.

## GitHub Actions

[CI](../.github/workflows/ci.yml) prüft Node.js 22 und 24 unter Linux sowie Node.js 24 unter macOS und Windows. Der Workflow ersetzt keine Prüfung mit einem angeschlossenen Beamer.

Der manuell startbare Workflow [Desktop preview builds](../.github/workflows/desktop-build.yml) erzeugt unsignierte Testartefakte. Er veröffentlicht keine GitHub-Release und verwendet `--publish never`.

## Desktop-Pakete

Erzeuge Pakete auf dem jeweiligen Zielsystem:

```sh
# macOS
npm run package:mac

# Windows
npm run package:win
```

Die Ausgaben liegen unter `release/`. mpv wird nicht gebündelt. Die Paketierung ist von der Signierung und macOS-Notarisierung getrennt; derzeit werden keine signierten Installationspakete zugesichert.

## Entwicklungsregeln

- Betriebssystem-, Datei- und Playerzugriffe bleiben im Electron-Hauptprozess.
- Erweitere die Preload-API nur um konkrete, überprüfbare Aktionen.
- Zugangsdaten bleiben außerhalb von Projektdateien und dürfen nicht in Logs erscheinen.
- Speichern, Vorschau und Verbindungstest dürfen keine Lampen schalten.
- Fehler bei Home Assistant dürfen die Videowiedergabe nicht stoppen.
- Aktualisiere Anleitung und Typen, wenn sich ein Bedienablauf oder Schnittstellenvertrag ändert.

Mehr zum Aufbau steht in [Architektur](architecture.md), zum Beitragen in [CONTRIBUTING.md](../CONTRIBUTING.md).
