# Geräteprüfung vor einer öffentlichen Version

[← Zur Projektübersicht](../README.md) · [Projektziel](../GOAL.md)

Die automatischen Prüfungen und der Paketbau ersetzen keinen Test im Kinoraum. Dieses Protokoll ist für **jeden** macOS- und Windows-Aufbau auszufüllen, bevor Lichtspiel als vorführbereit bezeichnet wird. Verwende eigene kurze Testvideos ohne persönliche Daten. Die unsignierten Testpakete stehen als zeitlich begrenzte Artefakte im [Desktop-Build-Workflow](../.github/workflows/desktop-build.yml); mpv muss separat installiert werden.

## Aufbau erfassen

| Angabe                                                    | Wert |
| --------------------------------------------------------- | ---- |
| Datum, Betriebssystem und Version                         |      |
| Rechner und CPU-Architektur                               |      |
| Lichtspiel-Commit / Paket                                 |      |
| mpv-Version und Installationsweg                          |      |
| Beamer, Kabel/Adapter und Bildschirmmodus                 |      |
| Audioausgabe und Verstärker/Lautsprecher                  |      |
| Testdateien: Container, Video- und Audiocodec             |      |
| Home Assistant, Lampenmodell und Netzwerk (falls genutzt) |      |

## Vorführung prüfen

Trage für jeden Schritt **Bestanden**, **Fehlgeschlagen** oder **Nicht zutreffend** und eine kurze Beobachtung ein. Prüfe am Beamer und am Lautsprecher, nicht nur in der Regieansicht.

| Schritt                                                                             | macOS | Windows | Beobachtung |
| ----------------------------------------------------------------------------------- | ----- | ------- | ----------- |
| App aus dem Paket starten und mpv erkennen                                          |       |         |             |
| Beamer als erweiterten Bildschirm wählen; Bild landet dort                          |       |         |             |
| Ton über das gewählte HDMI-Gerät oder Audiointerface ausgeben                       |       |         |             |
| Werbung → Trailer → Film ohne Eingriff abspielen                                    |       |         |             |
| Mehrere Clips unterschiedlicher Auflösung und Bildrate abspielen                    |       |         |             |
| Einen Film von mindestens 90 Minuten ohne Schlafmodus durchlaufen lassen            |       |         |             |
| Pause und Fortsetzen erhalten Bild, Ton und Clipposition                            |       |         |             |
| Schwarzbild pausiert Bild und Ton; Fortsetzen stellt beides wieder her              |       |         |             |
| Zum nächsten Clip wechseln; danach regulär beenden                                  |       |         |             |
| Vor dem Start eine Datei verschieben: Startprüfung meldet den Fehler                |       |         |             |
| Vor dem Start Beamer entfernen: Startprüfung meldet den Fehler                      |       |         |             |
| Startzeit für eine spätere Uhrzeit setzen und genau einmal ausführen                |       |         |             |
| Verpassten geplanten Start nach Schlaf oder Neustart verständlich melden            |       |         |             |
| App während einer Vorstellung schließen und wieder öffnen: Zustand ist verständlich |       |         |             |

## Optional: Lichtsteuerung

Die folgenden Schritte nur mit einer bewusst ausgewählten Testlampe durchführen. **Licht jetzt testen** sendet einen echten Befehl.

| Schritt                                                      | Ergebnis | Beobachtung |
| ------------------------------------------------------------ | -------- | ----------- |
| Verbindungstest und Vorschau verändern kein Licht            |          |             |
| Vorprogramm-Regel beim ersten Werbe-/Trailer-/Intro-Clip     |          |             |
| Hauptfilm-Regel beim Filmstart                               |          |             |
| Pause und Fortsetzen wenden die erwartete Regel an           |          |             |
| Ende oder Stopp wendet die Ende-Regel an                     |          |             |
| Netzwerkfehler wird gemeldet, ohne die Wiedergabe zu stoppen |          |             |

Ein Fehlerbericht sollte den betroffenen Schritt, den sichtbaren Zustand in Lichtspiel, das Ergebnis auf Beamer/Lautsprecher/Lampe und die genauen Geräteangaben enthalten. Zugangstoken, private Videodateien und persönliche Daten gehören nicht in öffentliche Issues.
