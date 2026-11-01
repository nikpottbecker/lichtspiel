# Änderungen

## 0.1.0 — Erste Entwicklungsvorschau

### Hinzugefügt

- Desktop-Grundlage für macOS und Windows mit React, TypeScript und Electron.
- Einrichtungsassistent für mpv, Wiedergabebildschirm und Audioausgabe.
- Lokale Mediathek, Medienkategorien, Suche und sortierbarer Vorführablauf.
- Gesamtlaufzeit, klare Regieansicht und einmalige Startplanung.
- mpv-Wiedergabesteuerung mit Pause, Fortsetzen, Clipwechsel, Stopp und Schwarzbild.
- Home-Assistant-Verbindung mit verschlüsselter Tokenablage und vier Lichtregeln.
- Getrennte Aktionen für Verbindungstest, Lichtvorschau und ausdrücklichen Gerätetest.
- Browser-Vorschau mit lokalen Videokopien, separatem Ausgabefenster und Wiedergabefreigabe.
- Automatisierte Prüfungen und Anleitungen zu Einrichtung, Entwicklung und Lichtsteuerung.

### Überarbeitet

- Die Regieansicht zeigt Medien als kompakte Ablaufliste mit Dateidetails und Ausgabestatus.
- Eine sichtbare Startprüfung meldet fehlende Medien, mpv und nicht verbundene Ausgabegeräte vor der Vorstellung.
- Während der Wiedergabe sind aktueller und nächster Clip samt Laufzeit direkt sichtbar.
- Navigation, Mediathek, Einrichtung und Lichtsteuerung nutzen eine einheitlichere, ruhigere Gestaltung.

### Stand der Erprobung

Build, Logiktests und Browserabläufe wurden geprüft. Die Steuerung eines echten mpv-Prozesses wurde unter Linux mit Nullausgabe getestet. Reale Bildschirm- und Tonprüfungen unter macOS/Windows sowie Tests mit einer Home-Assistant-Instanz bleiben offen.

Es wurden noch keine signierten Desktop-Installationspakete veröffentlicht. Die Version enthält keine DCP/KDM-Wiedergabe und keine Zusicherung bildgenauer Clipübergänge.
