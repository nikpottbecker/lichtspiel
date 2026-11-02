<p align="center">
  <img src="docs/assets/cover.png" alt="Lichtspiel-Banner mit weißem Projektorstrahl und Kinoleinwand" width="100%">
</p>

<h1 align="center">Lichtspiel</h1>

<p align="center">
  <strong>Dein Ablauf am Rechner. Dein Film auf der großen Leinwand.</strong><br>
  Eine offene Kinoregie für Werbung, Trailer, Filme und das passende Licht.
</p>

<p align="center">
  <a href="https://github.com/nikpottbecker/lichtspiel/actions/workflows/ci.yml"><img src="https://github.com/nikpottbecker/lichtspiel/actions/workflows/ci.yml/badge.svg" alt="CI-Prüfungen"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/Lizenz-MIT-e5e5e5?labelColor=202020" alt="Lizenz: MIT"></a>
  <a href="docs/roadmap.md"><img src="https://img.shields.io/badge/Status-0.1.0%20Preview-e5e5e5?labelColor=202020" alt="Status: 0.1.0 Preview"></a>
  <a href="docs/getting-started.md"><img src="https://img.shields.io/badge/Zielplattformen-macOS%20%26%20Windows-d8d8d8?labelColor=202020" alt="Zielplattformen: macOS und Windows"></a>
</p>

<p align="center">
  <a href="#schnellstart">Schnellstart</a> ·
  <a href="docs/getting-started.md">Erste Vorstellung</a> ·
  <a href="docs/home-assistant.md">Lichtsteuerung</a> ·
  <a href="docs/roadmap.md">Roadmap</a> ·
  <a href="GOAL.md">Projektziel</a> ·
  <a href="CONTRIBUTING.md">Mitmachen</a>
</p>

---

Lichtspiel bringt den kleinen Filmabend in einen vorbereiteten Ablauf: erst Werbung, dann Trailer, schließlich der Hauptfilm. Du bedienst die Vorstellung am Computer, während ein eigener Player das Bild auf den Beamer ausgibt. Auf Wunsch dimmt Home Assistant dazu die Kinolichter.

Für Heimkinos, Vereine und eigene Filmprojekte. Lokal auf deinem Rechner, ohne Lichtspiel-Konto.

> [!NOTE]
> **Version 0.1.0 ist eine Entwicklungsvorschau aus dem Quellcode.** Signierte Installationspakete sind noch nicht veröffentlicht. Beamer, Audio und reale Lampen müssen am jeweiligen Mac- oder Windows-Aufbau geprüft werden.

**Native Desktop-Vorschau:** Der Umbau auf eine Oberfläche aus Qt Widgets läuft. Sie verwendet keinen Chromium-Renderer; mpv bleibt der getrennte Player für die Leinwand. [Start, Funktionen und Grenzen der Qt-Version →](native/README.md)

<p align="center">
  <img src="docs/assets/native-preview.png" alt="Native Lichtspiel-Regie mit Leinwandvorschau, Ablauf und Vorführtasten" width="100%">
</p>

<p align="center">
  <img src="docs/assets/native-setup.png" alt="Bild- und Tonausgabe in der nativen Lichtspiel-App" width="100%">
</p>
<p align="center"><sub>Native Qt-App unter Linux aufgenommen. Echte Bildschirme, Ton und Beamer müssen am jeweiligen Vorführrechner geprüft werden.</sub></p>

Während der Vorstellung zeigt die Regieansicht den laufenden Clip, seine Restzeit und das nächste Element im Ablauf.

<p align="center">
  <img src="docs/assets/native-live-light-small.png" alt="Fest sichtbare Vorführsteuerung während die Lichtseite geöffnet ist" width="100%">
</p>

## Alles für den Ablauf

| Vorbereiten                                                                                                | Vorführen                                                                                                     |
| ---------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| **Geführte Einrichtung** — Player, Bildschirm und Tonausgabe auswählen; Testkarte direkt am Beamer prüfen. | **Getrennte Ausgabe** — Bedienung am Rechner, Video über mpv auf dem gewählten Bildschirm.                    |
| **Mediathek** — lokale Dateien importieren und als Werbung, Trailer, Intro oder Film einordnen.            | **Direkte Kontrolle** — starten, pausieren, fortsetzen, zum nächsten Clip wechseln oder Schwarzbild schalten. |
| **Ablaufeditor** — Clips mit Pfeilbuttons ordnen, Laufzeiten und Reihenfolge prüfen.                       | **Geplanter Beginn** — die Vorstellung einmalig zu einer festgelegten Uhrzeit starten.                        |
| **Lokales Speichern** — den Ablauf beim nächsten Öffnen wiederfinden.                                      | **Lichtregeln** — Helligkeit und Dimmzeit passend zu Vorprogramm, Film, Pause und Ende einstellen.            |
| **Startprüfung** — fehlende Medien, Player und Ausgabegeräte vor dem Beginn erkennen.                      | **Live-Ansicht** — aktuellen und nächsten Clip samt Restzeit im Blick behalten.                               |

Ein geplanter Start setzt eine geöffnete App und einen laufenden Rechner voraus. Schwarzbild pausiert Bild und Ton. Die Regieansicht prüft Medien, Player und Ausgabe; die Desktop-App prüft die Dateien beim tatsächlichen Start erneut.

## Schnellstart

Du brauchst **Git**, **Python 3.12 oder neuer** und für die Desktop-Wiedergabe **[mpv](https://mpv.io/installation/)**. Auf macOS:

```sh
git clone https://github.com/nikpottbecker/lichtspiel.git
cd lichtspiel
python3 -m venv .venv-native
.venv-native/bin/python -m pip install -r native/requirements.txt
.venv-native/bin/python native/main.py
```

Unter Windows nutzt du nach dem Klonen `py -3.12 -m venv .venv-native`, dann `.\.venv-native\Scripts\python.exe -m pip install -r native/requirements.txt` und `.\.venv-native\Scripts\python.exe native\main.py`.

Auf macOS lässt sich mpv beispielsweise mit `brew install mpv` installieren. Unter Windows wählst du einen Build über die [mpv-Installationsseite](https://mpv.io/installation/). Im Einrichtungsassistenten kannst du den Player bei Bedarf selbst auswählen.

**Erst die Browser-Vorschau ausprobieren?** Installiere Node.js 22 oder 24, führe `npm ci` aus und starte `npm run dev:web`. Sie benötigt kein mpv.

Die [Startanleitung](docs/getting-started.md) führt vom angeschlossenen Beamer bis zur ersten Vorstellung und erklärt häufige Probleme.

## Desktop und Browser

| Funktion                                | Desktop-App                      | Browser-Vorschau                   |
| --------------------------------------- | -------------------------------- | ---------------------------------- |
| Einrichtung, Mediathek und Ablaufeditor | Ja                               | Ja                                 |
| Lokale Videos abspielen                 | mpv                              | HTML-Video, abhängig vom Browser   |
| Medien speichern                        | Verweise auf die Originaldateien | Kopien im lokalen Browserspeicher  |
| Bildschirm und Tonausgabe wählen        | Ja                               | Ausgabefenster manuell verschieben |
| Automatisch zur Startzeit beginnen      | Ja, solange die App geöffnet ist | Nein                               |
| Home-Assistant-Lampen steuern           | Optional                         | Nur Vorschau, keine Gerätebefehle  |

## Licht aus. Film an.

Home Assistant verbindet Lichtspiel mit einer Lampe oder Lichtgruppe in deinem Kinoraum. Für jede Situation bestimmst du selbst Helligkeit und Übergangszeit.

| Moment                      | Voreinstellung |
| --------------------------- | -------------- |
| Werbung, Trailer oder Intro | 20 %           |
| Hauptfilm                   | Aus            |
| Pause                       | 40 %           |
| Ende oder manueller Stopp   | 80 %           |

<p align="center">
  <img src="docs/assets/native-room-plan.png" alt="Nativer 2D-Raumplan mit vier beispielhaften Lichtmarkierungen" width="100%">
</p>

Die Automatik ist anfangs ausgeschaltet. Verbindungstest und Vorschau verändern kein Licht; der Knopf **Licht jetzt testen** sendet ausdrücklich einen Gerätebefehl. Ein Lichtfehler unterbricht die Filmwiedergabe nicht.

**[Home Assistant einrichten →](docs/home-assistant.md)**

## Ein klarer erster Stand

Die [native Qt-Version](native/README.md) ist der aktuelle Desktop-Schwerpunkt. Die bisherige Electron-Version bleibt für Gerätevergleiche im Repository; beide verwenden **mpv** als separaten Wiedergabeprozess.

Automatisierte Tests decken Ablaufplanung, Dateiprüfung, Player-Protokoll und Lichtregeln ab. Browser-Tests prüfen außerdem den Weg vom Import bis zur tatsächlichen Videoausgabe. Die mpv-Steuerung wurde unter Linux mit echten Testclips und Nullausgabe geprüft; das ersetzt keine Bild- und Tonprüfung auf macOS oder Windows.

Der aktuelle Umfang umfasst weder DCP/KDM-Kinopakete noch Projektor- und Vorhangautomation. Nahtlose oder bildgenaue Übergänge zwischen beliebigen Dateien sind nicht zugesichert.

## Dokumentation

| Du möchtest …                              | Hier geht es weiter                                                                         |
| ------------------------------------------ | ------------------------------------------------------------------------------------------- |
| die erste Vorstellung einrichten           | [Startanleitung](docs/getting-started.md)                                                   |
| einen Vorführrechner praktisch prüfen      | [Geräteprüfung](docs/hardware-test.md)                                                      |
| deine Kinolichter anbinden                 | [Home Assistant](docs/home-assistant.md)                                                    |
| lokal entwickeln, testen oder Pakete bauen | [Entwicklung](docs/development.md)                                                          |
| den technischen Aufbau verstehen           | [Architektur](docs/architecture.md)                                                         |
| den nächsten Ausbau verfolgen              | [Roadmap](docs/roadmap.md) · [Änderungen](CHANGELOG.md)                                     |
| einen Fehler melden oder mitentwickeln     | [Mitmachen](CONTRIBUTING.md) · [Issues](https://github.com/nikpottbecker/lichtspiel/issues) |

## Lizenz und Grundlagen

**Copyright © 2026 Nik Pottbecker.** Der eigene Anwendungscode steht unter der **[MIT-Lizenz](LICENSE)**.

Wer Kopien oder wesentliche Teile des Codes weitergibt, muss den Copyright-Hinweis mit **Nik Pottbecker** und den MIT-Lizenztext beibehalten. Die MIT-Lizenz verlangt keine zusätzliche sichtbare Nennung in der Benutzeroberfläche oder Werbung.

mpv wird separat installiert und behält seine eigene Lizenz. Alle weiteren Hinweise findest du unter [Fremdsoftware und Lizenzen](THIRD_PARTY.md).

Lichtspiel ist ein eigenständiges Projekt. Es übernimmt keinen Quellcode aus QLab, PreShow Experience oder CasparCG.
