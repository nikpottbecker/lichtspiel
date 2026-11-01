# Änderungen

## 0.1.0 — Erste Entwicklungsvorschau

### Hinzugefügt

- Desktop-Grundlage für macOS und Windows mit React, TypeScript und Electron.
- Einrichtungsassistent für mpv, Wiedergabebildschirm und Audioausgabe.
- Lokale Mediathek, Medienkategorien, Suche und sortierbarer Vorführablauf.
- Gesamtlaufzeit, Zeitachse und einmalige Startplanung.
- mpv-Wiedergabesteuerung mit Pause, Fortsetzen, Clipwechsel, Stopp und Schwarzbild.
- Home-Assistant-Verbindung mit verschlüsselter Tokenablage und vier Lichtregeln.
- Getrennte Aktionen für Verbindungstest, Lichtvorschau und ausdrücklichen Gerätetest.
- Browser-Vorschau mit lokalen Videokopien, separatem Ausgabefenster und Wiedergabefreigabe.
- Automatisierte Prüfungen und Anleitungen zu Einrichtung, Entwicklung und Lichtsteuerung.

### Stand der Erprobung

Build, Logiktests und Browserabläufe wurden geprüft. Die Steuerung eines echten mpv-Prozesses wurde unter Linux mit Nullausgabe getestet. Reale Bildschirm- und Tonprüfungen unter macOS/Windows sowie Tests mit einer Home-Assistant-Instanz bleiben offen.

Es wurden noch keine signierten Desktop-Installationspakete veröffentlicht. Die Version enthält keine DCP/KDM-Wiedergabe und keine Zusicherung bildgenauer Clipübergänge.
