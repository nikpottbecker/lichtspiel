# Native Desktop-Vorschau

Die neue Lichtspiel-Oberfläche besteht aus **Qt Widgets (PySide6)**. Sie enthält keinen eingebetteten Browser und startet keinen Webserver. Die Videodekodierung und Leinwandausgabe bleiben im eigenen mpv-Prozess; Dateiprüfung, Import, Gerätesuche und Home-Assistant-Aufrufe laufen außerhalb des UI-Threads.

Die Qt-Version ist eine **Entwicklungsvorschau**, keine freigegebene Kinosaal-Version. Insbesondere Bildschirmauswahl, Ton, lange Filme, App-Beenden und die System-Schlüsselbunde müssen auf echten Macs und Windows-Rechnern mit Beamer geprüft werden. Die [Geräteprüfung](../docs/hardware-test.md) dient als Protokoll.

## Aus dem Quellcode starten

Benötigt werden Python 3.12 oder neuer und [mpv](https://mpv.io/installation/). Aus dem Repository:

```sh
python -m venv .venv-native
# macOS: source .venv-native/bin/activate
# Windows PowerShell: .venv-native\Scripts\Activate.ps1
python -m pip install -r native/requirements.txt
python native/main.py
```

Die App erkennt mpv auf dem Suchpfad und an üblichen Installationsorten; andernfalls lässt sich die ausführbare Datei unter **Bild & Ton** auswählen. Dort zuerst den Beamer wählen und die Testkarte prüfen. Danach einen kurzen Clip für Bildbewegung und Ton abspielen.

## Stand des Umbaus

| Bereich                                                   | Qt-Vorschau                                                                                    |
| --------------------------------------------------------- | ---------------------------------------------------------------------------------------------- |
| Projektdatei, Mediathek, Kategorien und geordneter Ablauf | Vorhandene Electron-Projektdatei wird gelesen und weiterverwendet                              |
| mpv-Wiedergabe                                            | Separater Prozess mit asynchroner IPC; Pause, Fortsetzen, Schwarzbild, nächster Clip und Stopp |
| Live-Regie                                                | Getrennte Balken für Clip und Gesamtablauf, Restzeiten und nächster Clip bleiben sichtbar      |
| Player-Überwachung                                        | Eine ausbleibende IPC-Antwort wird nach 12 Sekunden als Fehler gemeldet                        |
| Bild & Ton                                                | Bildschirmauswahl, Tongerät, mpv-Erkennung und native mpv-Testkarte                            |
| Startprüfung und Startplanung                             | Dateiprüfung im Hintergrund; einmaliger Start bei offener App                                  |
| Home Assistant                                            | Mehrere Lampen, Szenen oder Helligkeit je Ereignis, optional Schwarzbild, Gerätesuche          |
| Kleine Fenster                                            | Regietasten bleiben sichtbar, der Ablauf scrollt                                               |

Der Bildschirm wird für die Qt-Version als `nativeDisplayId` in `settings.json` gespeichert. Dadurch überschreibt sie die Electron-Bildschirmauswahl im gemeinsamen Projekt nicht. Öffne **nicht beide Apps gleichzeitig** mit demselben Projekt. Home-Assistant-Regeln können aus der bisherigen Konfiguration übernommen werden; das verschlüsselte Electron-Token ist nicht übertragbar. Gib es einmal in der Qt-App neu ein und aktiviere die Automatik dort ausdrücklich.

Speichere auf der Lichtseite zuerst Adresse und Token mit ausgeschalteter Automatik. Danach kannst du **Lampen laden** und Ziele auswählen. Bis zu 20 `light.*`-Entitäten oder Lichtgruppen lassen sich gemeinsam dimmen. Jede Regel wählt entweder Helligkeit und Übergangszeit oder eine Home-Assistant-Szene; Szenen eignen sich für Farben und mehrere Räume. Die Schwarzbild-Regel ist standardmäßig **aus**. **Lampen laden** und **Verbindung prüfen** lesen nur Daten. Geänderte Regeln müssen vor einem Test gespeichert werden. Wiederholte Clips derselben Vorprogramm-Kategorie senden keinen doppelten Befehl; ausstehende ältere Automatikbefehle werden bei schnellen Wechseln verworfen. Fehler erscheinen ohne modales Fenster und stoppen den Film nicht.

![Qt-Lichtregeln mit mehreren Lampen und einer Szene](../docs/assets/native-lighting.png)

Die Vorschau liefert noch keine signierten Installationspakete. Der [Qt-Build-Workflow](../.github/workflows/native-desktop.yml) erzeugt unsignierte Testartefakte für macOS und Windows. mpv wird separat installiert.

## Prüfen und paketieren

```sh
python -m unittest discover -s native/tests -v
python native/build.py
```

Der Paketbau nutzt PyInstaller und schreibt nach `release/native/`. Die Tests enthalten einen simulierten mpv-IPC-Prozess; sie ersetzen keine Kontrolle von Bild und Ton auf einem realen Beamer.
