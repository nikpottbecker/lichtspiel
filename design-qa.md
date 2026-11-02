# Visuelle Prüfung der nativen App

Die aktuellen Aufnahmen zeigen die **Qt-Desktop-App** im monochromen Design. Sie wurden unter Linux mit Beispieldaten und einer simulierten Testkarte erstellt. Sie belegen das Layout, nicht die Bild- oder Tonqualität eines echten Beamers.

| Ansicht         | Bild                                                                     | Geprüfter Zustand                                                   |
| --------------- | ------------------------------------------------------------------------ | ------------------------------------------------------------------- |
| Regie           | [Leinwandvorschau und Ablauf](docs/assets/native-preview.png)            | Vorschau, Clip- und Gesamtfortschritt, fest sichtbare Vorführtasten |
| Mediathek       | [Leerer Zustand](docs/assets/native-library.png)                         | Medienimport sichtbar; Aktionen ohne Auswahl deaktiviert            |
| Bild & Ton      | [Einrichtung](docs/assets/native-setup.png)                              | Player-, Bildschirm-, Ton- und Vorschaueinstellungen                |
| Licht           | [Raumplan](docs/assets/native-room-plan.png)                             | Vier Marker und Planbedienung direkt nach einem Wechsel             |
| Lichtregeln     | [Regeln](docs/assets/native-lighting.png)                                | Ereignisse, Helligkeit und Übergänge in einem eigenen Bereich       |
| Kleines Fenster | [Live-Regie auf der Lichtseite](docs/assets/native-live-light-small.png) | Vorführtasten bleiben beim Seitenwechsel erreichbar                 |

Die Navigation ist in einem schwebenden Balken angeordnet. Weiß markiert die aktuelle Seite und die wichtigste Aktion; die übrigen Flächen bleiben in Schwarz und Grau. Die Lichttiefe im Seitenkopf ist statisch und läuft nur in der Bedienoberfläche. Die Leinwandausgabe bleibt ein getrennter mpv-Prozess.

Bei 1260 × 900 Pixeln wurden alle vier Hauptansichten visuell geprüft. Die Lichtseite trennt Verbindung, Raumplan und Regeln; der Raumplan ist ohne langes Scrollen erreichbar. Bei 900 × 640 Pixeln wird der Seitenkopf kompakter und die Vorführtasten bleiben sichtbar. Regressionstests prüfen den Seitenwechsel, den kompakten Kopf und getrennte Scrollbereiche. Die nativen Tests und die macOS-/Windows-Paketjobs laufen in der CI. Farb- und Kontrastwirkung auf echten Monitoren sowie die Bedienung mit Screenreadern brauchen weitere praktische Prüfung.
