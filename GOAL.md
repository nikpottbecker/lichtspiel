# Ziel: Lichtspiel als verlässliche Kinoregie

Lichtspiel soll einen vorbereiteten Filmabend auf macOS und Windows sicher und angenehm steuern: Werbung, Trailer und Film in einer klaren Reihenfolge, Ausgabe auf dem gewählten Bildschirm, verständliche Eingriffe während der Vorstellung und optionales Licht über Home Assistant.

„Fertig“ bedeutet hier einen überprüfbaren Qualitätsstand, kein Versprechen perfekter Wiedergabe auf jeder Hardware. Jede Etappe bekommt sichtbares Verhalten, automatisierte Prüfungen und, wo nötig, einen Test an echten Geräten.

## Qualitätsmaßstab

1. **Vor der Vorstellung:** Fehlende Dateien, Player und Ausgabegeräte sind erkennbar, bevor das Publikum im Saal sitzt. Eine geplante Vorstellung bleibt nach dem Neustart nachvollziehbar; ein Start findet nur zu einer gültigen Zeit statt.
2. **Während der Vorstellung:** Aktueller und nächster Clip, Fortschritt und Ausgabestatus sind auf einen Blick lesbar. Pause, Fortsetzen, nächster Clip, Stopp und Schwarzbild verhalten sich vorhersehbar. Fehler nennen eine konkrete nächste Handlung.
3. **Organisation:** Mehrere Vorstellungen und wiederverwendbare Abläufe lassen sich verwalten, ohne Medien unbemerkt zu verschieben oder zu duplizieren. Import und Export erhalten die Reihenfolge und erklären fehlende Dateien.
4. **Gestaltung:** Eine konsistente Schrift-, Farb-, Abstands- und Komponentenstruktur gilt für Einrichtung, Mediathek, Regie und Lichtsteuerung. Tastaturbedienung, Fokus, Kontrast und kleinere Fenster werden geprüft.
5. **Desktop-Qualität:** Builds für macOS und Windows sind reproduzierbar. Beamerwechsel, Bild und Ton, längere Filme und Home Assistant werden auf echten Geräten getestet. Installationspakete erscheinen erst mit dokumentiertem Teststand.

## Aktuelle Etappen

- [x] Grundlegender Ablauf mit mpv, Browser-Vorschau, Startplanung und Home Assistant.
- [x] Ruhigere Regieansicht mit gesondertem Fokus während der Wiedergabe.
- [x] Sichtbare Startprüfung für Medien, Player und Ausgabe.
- [ ] Gemeinsames Designsystem ohne überlagerte Altregeln; alle vier Hauptansichten visuell geprüft.
- [ ] Wiederherstellung und Vorführprotokoll bei Unterbrechungen.
- [ ] Mehrere gespeicherte Vorstellungen und wiederverwendbare Vorlagen.
- [ ] Praktische Testmatrix für macOS, Windows, Beamer, Ton und Home Assistant.
- [ ] Signierte, dokumentierte Installationspakete.

Die offenen Punkte werden in dieser Reihenfolge bearbeitet, wenn neue Erkenntnisse nicht eine andere Reihenfolge begründen. [Roadmap](docs/roadmap.md) und [Entwicklung](docs/development.md) enthalten weitere Details.
