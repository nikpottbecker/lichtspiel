# Designprüfung: Regieansicht

**Ergebnis:** `final result: passed`

## Vergleichsbasis

- Visuelle Richtung: [Regiepult-Entwurf](docs/assets/regiepult-concept.png), 1487 × 1058 Pixel.
- Gerenderte Umsetzung: [Regieansicht](docs/assets/show-control.png), 1536 × 1091 Pixel bei 1536 × 1060 CSS-Pixeln und DPR 1.
- Zustand: vorbereitete Vorstellung mit drei Beispielmedien, Browser-Ausgabe gewählt, Wiedergabe noch nicht gestartet. Der Entwurf zeigt vier beispielhafte Medien und das zweite Element als Auswahl. Deshalb wurden Textinhalt und Anzahl der Zeilen nicht als pixelgenauer Maßstab gewertet.
- Für den Gesamtvergleich wurden beide Ansichten auf 1440 × 1024 Pixel normalisiert und gemeinsam betrachtet. Der Ablauf und der Detailbereich wurden zusätzlich als gemeinsamer Ausschnitt geprüft. Die Vergleichsbilder liegen lokal unter `/tmp/lichtspiel-design-qa.png` und `/tmp/lichtspiel-design-qa-focus.png`.

## Befunde

Keine offenen P0-, P1- oder P2-Befunde. Die visuelle Hierarchie des Entwurfs ist übernommen: Betriebsstatus oben, zeilenförmiger Ablauf als Hauptfläche, Dateidetails rechts und Wiedergabesteuerung unten. Die frühere Schein-Vorschau und doppelte Zeitachse sind entfernt.

- **Schrift:** DM Sans bleibt als Projektschrift. Haupttitel, Cue-Titel und Betriebsstatus sind klar abgestuft; Zeitangaben verwenden tabellarische Ziffern. Die kleinen Tabellenüberschriften sind bewusst nachgeordnet.
- **Abstände und Raster:** Die Ablaufliste verwendet Zeilentrenner und eine schmale Auswahlmarkierung. Der Detailbereich hat eine eigene Spalte. Bei nur drei Elementen bleibt freier Platz für längere Vorstellungen.
- **Farben:** Graphit, Warmweiß und ein einzelnes Bernsteinsignal bestimmen die Ansicht. Der Akzent markiert Auswahl, Wiedergabe und Hauptaktion.
- **Bilder und Symbole:** Die Regieansicht benötigt keine Bildmotive. Standardaktionen verwenden die bestehende Icon-Bibliothek; es gibt keine Platzhaltervorschau.
- **Text und Produktwahrheit:** Der Entwurf zeigt zusätzliche Metadaten und Cue-Bedingungen. Die Umsetzung zeigt nur tatsächlich vorhandene Daten und Funktionen. „Geplant“ kennzeichnet ein importiertes Element ohne vorgezogene Dateiprüfung; Beispieldateien sind ausdrücklich als nicht abspielbar markiert.

## Prüfung und Verlauf

Die erste mobile Aufnahme hatte horizontalen Überlauf durch die Beschriftung des Importknopfs. Auf schmalen Fenstern ist dieser Knopf nun ein beschriftetes Icon mit unverändertem zugänglichem Namen. Die erste Browserprüfung erwartete außerdem den bisherigen Endstatus „Vorstellung beendet“; dieser ist wieder sichtbar. Der erste Vergleich zeigte zu kleine Sekundärtexte und eine zu schmale Detailspalte; Schriftgrößen, Zeilenhöhe und Spaltenbreite wurden danach erhöht.

Die aktualisierte Desktop-Ansicht, die mobile Ansicht und die laufende Vorstellung wurden im lokalen Chromium geöffnet. Geprüft wurden Einrichtung, Import, Reihenfolge, Speichern, echte Browser-Wiedergabe, Pause, Schwarzbild, Fortsetzen, Ende, Mediathek und Lichtvorschau. Keine Seitenfehler; kein horizontaler Überlauf bei 390 Pixeln oder in der Live-Ansicht. `npm run test:browser` und `npm run check` sind erfolgreich. Physische Beamer und Lampen waren für diese Designprüfung nicht verbunden.

## Weitere Politur

- P3: Bei sehr langen Abläufen könnte ein dauerhaft sichtbarer Spaltenkopf das Lesen erleichtern.
