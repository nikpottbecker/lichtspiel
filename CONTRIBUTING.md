# An Lichtspiel mitarbeiten

Danke für dein Interesse. Hilfreich sind verständliche Fehlerberichte, Erfahrungen mit echten Beameraufbauten, Verbesserungen der Bedienung und nachvollziehbare Codeänderungen.

## Fehler melden

Prüfe zuerst die [vorhandenen Issues](https://github.com/nikpottbecker/lichtspiel/issues). Ein guter Fehlerbericht enthält:

- Betriebssystem, CPU-Architektur und verwendete Lichtspiel-Version beziehungsweise Commit.
- Browser- oder Desktop-Modus; bei Desktop-Problemen zusätzlich die mpv-Version.
- Schritte vom Startzustand bis zum Fehler.
- Erwartetes und tatsächliches Verhalten.
- Bei Ausgabeproblemen: Bildschirmaufbau, Audioverbindung und Medienformat.

Kurze selbst erstellte Testclips sind leichter reproduzierbar als vollständige Filme. Entferne persönliche Pfade, Home-Assistant-Tokens und andere Zugangsdaten aus Screenshots und Protokollen.

## Eine Verbesserung vorschlagen

Beschreibe zuerst die Situation: Welche Aufgabe soll während der Vorbereitung oder Vorstellung einfacher werden? Ein kurzer Ablauf mit konkretem Beispiel ist hilfreicher als eine lange Funktionsliste.

Die [Roadmap](docs/roadmap.md) zeigt die derzeitige Richtung. Größere Änderungen an Wiedergabe, Speichern oder Geräteautomation sollten vor umfangreicher Implementierung in einem Issue besprochen werden.

## Code beitragen

1. Repository forken und einen eigenen Branch anlegen.
2. Die [Entwicklungsanleitung](docs/development.md) befolgen.
3. Eine möglichst zusammenhängende Änderung umsetzen und passende Prüfungen ausführen.
4. Bedienungs- oder Schnittstellenänderungen in der Dokumentation beschreiben.
5. Einen Pull Request mit Problem, Lösung und Prüfungen eröffnen.

```sh
npm ci
npm run check
```

Für Änderungen an der Oberfläche oder Wiedergabesteuerung sollten auch die Browserabläufe aus der Entwicklungsanleitung geprüft werden. Native Hardwaretests bitte konkret benennen; ein Browser-Test allein belegt keine Beamer- oder Audiofunktion.

## Worauf wir achten

- Die Oberfläche bleibt von Betriebssystemzugriffen getrennt.
- Ein Fehler bei einer Lichtaktion unterbricht keinen Film.
- Vorschau und Verbindungstest verändern keine Geräte.
- Laufende Vorstellungen dürfen nicht durch unerwartete Hintergrundaktionen ersetzt werden.
- Gespeicherte Benutzerdaten werden bei Fehlern nicht stillschweigend überschrieben.
- Dokumentation erklärt vorhandenes Verhalten und kennzeichnet offene Grenzen.

Eigener Projektcode steht unter MIT. Neue Abhängigkeiten müssen mit ihrer Lizenz und ihrem Zweck nachvollziehbar sein. Die separate mpv-Lizenz bleibt davon unberührt.
