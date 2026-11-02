# Ziel: Lichtspiel als verlässliche Kinoregie

Lichtspiel soll einen vorbereiteten Filmabend auf macOS und Windows sicher und angenehm steuern: Werbung, Trailer und Film in einer klaren Reihenfolge, Ausgabe auf dem gewählten Bildschirm, verständliche Eingriffe während der Vorstellung und optionales Licht über Home Assistant.

„Fertig“ bedeutet hier einen überprüfbaren Qualitätsstand, kein Versprechen perfekter Wiedergabe auf jeder Hardware. Jede Etappe bekommt sichtbares Verhalten, automatisierte Prüfungen und, wo nötig, einen Test an echten Geräten.

## Auftrag für jeden Lauf

Arbeite eigenständig an Lichtspiel weiter. Lies zuerst den aktuellen Code, die offenen Punkte in dieser Datei und die letzten Testergebnisse. Wähle die wichtigste überschaubare Verbesserung für die **native Qt-App auf macOS und Windows** und setze sie vollständig um. Priorisiere eine verlässliche Beamer- und Tonausgabe, eine während der Vorstellung stets bedienbare Regie, verständliche Fortschritts- und Fehleranzeigen, sichere Home-Assistant-Automation und eine ruhige, konsistente Gestaltung ohne generischen „Vibecoding“-Look. Die visuelle Richtung ist Schwarz, Weiß und Grau mit einer schwebenden Navigation und ruhiger Lichttiefe; vermeide ein Neon-Lila-Theme. Behalte mpv als getrennten Wiedergabeprozess und halte die App lokal und ohne Webserver nutzbar.

Prüfe die Änderung mit passenden Logik-, UI- und Pakettests; sieh neue Oberflächen auch im kleinen Fenster an. Dokumentiere Verhalten und Grenzen, aktualisiere die Aufgabenliste und veröffentliche geprüfte Änderungen im bestehenden GitHub-Repository. Behaupte keine erfolgreiche Beamer-, Audio- oder Lampenprüfung ohne einen Test am echten Gerät. Nenne am Ende des Laufs konkret, was verbessert wurde, welche Prüfungen bestanden haben und was als Nächstes offen ist. Beginne beim nächsten Lauf wieder mit dem wichtigsten offenen Punkt.

## Qualitätsmaßstab

1. **Vor der Vorstellung:** Fehlende Dateien, Player und Ausgabegeräte sind erkennbar, bevor das Publikum im Saal sitzt. Eine geplante Vorstellung bleibt nach dem Neustart nachvollziehbar; ein Start findet nur zu einer gültigen Zeit statt.
2. **Während der Vorstellung:** Aktueller und nächster Clip, Fortschritt und Ausgabestatus sind auf einen Blick lesbar. Pause, Fortsetzen, nächster Clip, Stopp und Schwarzbild verhalten sich vorhersehbar. Fehler nennen eine konkrete nächste Handlung.
3. **Organisation:** Mehrere Vorstellungen und wiederverwendbare Abläufe lassen sich verwalten, ohne Medien unbemerkt zu verschieben oder zu duplizieren. Import und Export erhalten die Reihenfolge und erklären fehlende Dateien.
4. **Gestaltung:** Eine konsistente Schrift-, Farb-, Abstands- und Komponentenstruktur gilt für Einrichtung, Mediathek, Regie und Lichtsteuerung. Tastaturbedienung, Fokus, Kontrast und kleinere Fenster werden geprüft.
5. **Desktop-Qualität:** Lichtspiel läuft lokal und offline ohne Browserfenster oder Server. Die Leinwand wird von einem eigenen mpv-Prozess ausgegeben. Builds für macOS und Windows sind reproduzierbar. Beamerwechsel, Bild und Ton, längere Filme und Home Assistant werden auf echten Geräten getestet. Installationspakete erscheinen erst mit dokumentiertem Teststand.

## Aktuelle Etappen

- [x] Grundlegender Ablauf mit mpv, Browser-Vorschau, Startplanung und Home Assistant.
- [x] Ruhigere Regieansicht mit gesondertem Fokus während der Wiedergabe.
- [x] Sichtbare Startprüfung für Medien, Player und Ausgabe.
- [x] Erste native Qt-Regie ohne Chromium mit eigenem mpv-Prozess und fest sichtbaren Vorführtasten.
- [x] Live-Fortschritt für Clip und Gesamtablauf sowie erweiterte Home-Assistant-Regeln in der Qt-Vorschau.
- [x] Bewusste Wiederaufnahme einer unterbrochenen Qt-Vorstellung nach Medien- und Ausgabeprüfung.
- [x] Live-Regie bleibt während der Wiedergabe auch auf Medien-, Einrichtungs- und Lichtseite sichtbar.
- [x] Native Kontrollvorschau aus dem laufenden mpv-Prozess und lokaler 2D-Raumplan für Lichtmarkierungen.
- [x] Kompakte Live-Regie mit unmittelbar sichtbarem Ablauf, eindeutig markiertem aktuellen Clip und ohne doppelte Vorschau.
- [x] Geführte native Ersteinrichtung mit Beamer-Sichtprüfung und Dateiprüfung vor dem Abschluss.
- [ ] Qt-Version auf realer macOS-/Windows-Hardware mit Beamer, Ton und Home Assistant abnehmen und erst dann als Standard festlegen.
- [x] Gemeinsames Designsystem ohne überlagerte Altregeln; alle vier Hauptansichten visuell geprüft.
- [ ] Vorführprotokoll für Start, Eingriffe, Clipwechsel und Fehler sowie weitere Wiederherstellungsfälle.
- [ ] Mehrere gespeicherte Vorstellungen und wiederverwendbare Vorlagen.
- [ ] Praktische Testmatrix für macOS, Windows, Beamer, Ton und Home Assistant.
- [ ] Signierte, dokumentierte Installationspakete.

Die offenen Punkte werden in dieser Reihenfolge bearbeitet, wenn neue Erkenntnisse nicht eine andere Reihenfolge begründen. Die [Geräteprüfung](docs/hardware-test.md) definiert die praktischen Tests; [Roadmap](docs/roadmap.md) und [Entwicklung](docs/development.md) enthalten weitere Details.
