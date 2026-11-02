# Licht passend zur Vorstellung

[← Zur Projektübersicht](../README.md)

Lichtspiel steuert über Home Assistant Kinolicht. Die bisherige Electron-App verwendet eine Lampe oder Lichtgruppe; die [native Qt-Vorschau](../native/README.md) kann mehrere Lampen und Szenen ansteuern. Die Verbindung läuft lokal von der Desktop-App zu Home Assistant. Im Browser gibt es nur eine Vorschau ohne Gerätezugriff.

## Verbindung einrichten

1. Richte deine Lampen in Home Assistant ein. Eine gemeinsam zu steuernde Gruppe muss dort als `light.*`-Entität verfügbar sein.
2. Erstelle in deinem Home-Assistant-Profil ein **langlebiges Zugriffstoken**.
3. Öffne in Lichtspiel **Lichtsteuerung** beziehungsweise in der Qt-App **Licht**. Lass die Automatik zunächst ausgeschaltet.
4. Trage die Basisadresse ein, zum Beispiel `http://homeassistant.local:8123`, und füge den Token ein. Speichere die Verbindung.
5. Klicke auf **Verbindung prüfen**. Der Test liest die erreichbaren Licht-Entitäten und Szenen, verändert aber keine Lampe. In der Qt-App müssen Änderungen vor dem Test gespeichert sein.
6. Wähle die Lampe oder Lichtgruppe aus und passe die Regeln an.
7. Aktiviere bei Bedarf **Automatisch steuern** und speichere erneut.

Die Adresse darf keine Zugangsdaten, `/api`-Erweiterung, Suchparameter oder Fragmente enthalten. Verwende eine direkt erreichbare Adresse: HTTP-Weiterleitungen werden nicht verfolgt.

## Regeln festlegen

| Regel       | Auslöser                                                    | Voreinstellung |
| ----------- | ----------------------------------------------------------- | -------------- |
| Vorprogramm | Ein Clip der Kategorie Werbung, Trailer oder Intro beginnt. | 20 %           |
| Hauptfilm   | Ein Clip der Kategorie Film beginnt.                        | 0 % / aus      |
| Pause       | Du pausierst die Vorstellung.                               | 40 %           |
| Schwarzbild | In der Qt-App optional beim Schwarzbild.                    | Deaktiviert    |
| Ende        | Der letzte Clip endet oder du stoppst die Vorstellung.      | 80 %           |

Jede Regel hat einen eigenen Aktivierungsschalter, einen Helligkeitswert und eine Übergangszeit. Ob eine Lampe sanft dimmen kann, hängt von ihrer Home-Assistant-Integration ab.

Beim **Fortsetzen** gilt wieder die Regel der aktuellen Clip-Kategorie. In der Electron-App löst **Schwarzbild** keine eigene Lichtaktion aus; in der Qt-App lässt sich dafür optional eine Regel aktivieren. Ende und Stopp verwenden den festgelegten Endwert; sie stellen nicht automatisch den Lampenzustand vor Beginn der Vorstellung wieder her. Das Schließen der App ist ebenfalls keine Wiederherstellung des vorherigen Zustands.

Die Qt-App kann bis zu 20 `light.*`-Entitäten oder Lichtgruppen gemeinsam ansteuern. Pro Moment wählst du **Helligkeit** oder eine `scene.*`-Entität. Nutze Home-Assistant-Szenen für Farben, komplexe Raumzustände und Geräte mit unterschiedlichen Fähigkeiten. Vorprogramm-Clips direkt hintereinander wiederholen denselben Lichtbefehl nicht. Bei schnellen Zustandswechseln werden noch ausstehende alte Automatikaktionen übersprungen.

In der nativen App gibt es zusätzlich einen lokalen **2D-Raumplan**. Speichere zuerst die gewünschten `light.*`-Ziele, wähle sie dann im Plan aus und ziehe ihre Marker an die passende Position. Ein eigenes Grundrissbild kann als Hintergrund geladen werden. Der Plan dient der Orientierung und verändert keine Lampen; nur aktivierte Regeln oder **Licht jetzt testen** senden Befehle. Markerpositionen und Grundrissbild werden lokal gespeichert, nicht an Home Assistant übertragen.

## Vorschau und echter Test

Nach Änderungen müssen die Regeln zuerst gespeichert werden.

- **Vorschau** beschreibt den geplanten Befehl. Es wird kein Gerätebefehl gesendet.
- **Verbindung prüfen** liest verfügbare Lampen. Es wird kein Licht verändert.
- **Licht jetzt testen** sendet die gewählte Regel sofort an das ausgewählte Licht. Dafür müssen Verbindung, Ziel und Regel aktiv sein.

In der Qt-App zeigt die Regelvorschau die **gespeicherte** Aktion. **Lampen laden** liest verfügbare `light.*`-Entitäten; du kannst mehrere hinzufügen. Der Verbindungstest prüft dort auch, ob gespeicherte Lampen und Szenen noch existieren.

Teste die Zielauswahl zuerst an deinem eigenen Aufbau. In der Entwicklungsumgebung wurden Home-Assistant-Antworten simuliert; keine reale Instanz oder Lampe wurde verbunden.

## Wie Fehler behandelt werden

Eine nicht erreichbare Lampe oder ein ungültiger Token unterbricht die Filmwiedergabe nicht. Lichtspiel meldet den Fehler separat. Die Qt-App zeigt automatische Lichtfehler ohne modales Fenster. Lesende Verbindungsabfragen werden bei einem kurzen Netzwerkfehler einmal wiederholt; schreibende Licht- und Szenenbefehle werden nicht automatisch doppelt gesendet. Aufeinanderfolgende Zeitfortschrittsmeldungen des Players erzeugen keine zusätzlichen Lichtbefehle.

| Meldung oder Verhalten                | Prüfen                                                                              |
| ------------------------------------- | ----------------------------------------------------------------------------------- |
| Verbindung nicht erreichbar           | Basisadresse, Port und Netzwerkverbindung des Desktop-Rechners.                     |
| Zugriff abgelehnt                     | Gültigkeit und Berechtigungen des Home-Assistant-Tokens.                            |
| Keine Lampe auswählbar                | Verbindung zuerst speichern und prüfen; die Entität muss unter `light.*` vorliegen. |
| Vorschau möglich, aber keine Änderung | Automatik, Regel und Zielauswahl müssen aktiviert und gespeichert sein.             |
| Licht schaltet statt zu dimmen        | Unterstützung von Helligkeit und Übergangszeit durch Lampe und Integration.         |
| Token nach Serverwechsel fehlt        | Für den neuen Server muss ein neuer Token eingegeben werden.                        |

## Zugangsdaten

Die Electron-App speichert Token und zugehörige Serveradresse gemeinsam verschlüsselt mit `safeStorage`. Die Qt-App speichert ihren Token separat im System-Schlüsselbund; ihre Projekt- und Lichtdateien enthalten keinen Token. Das Electron-Token kann aus technischen Gründen nicht in die Qt-App übernommen werden und muss dort einmal neu eingegeben werden.

Ist sichere Speicherung nicht verfügbar, gibt es keinen Rückfall auf eine Klartextdatei. Ein macOS-Schlüsselbund beziehungsweise die passende Windows-Speicherfunktion muss verfügbar sein. Unter Linux wird der `basic_text`-Fallback abgelehnt.

Der Token gehört nicht in Showdateien, Screenshots, Issues oder dieses Repository. Bei einem Serverwechsel wird ein gespeicherter Token nicht an den neuen Server weitergegeben. Die Browser-Vorschau speichert keine Home-Assistant-Zugangsdaten.

Technische Details stehen in der [Architektur](architecture.md).
